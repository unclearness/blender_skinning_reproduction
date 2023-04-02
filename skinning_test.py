import json
import numpy as np
import obj_io


# http://graphics.cs.cmu.edu/courses/15-466-f17/notes/skinning.html
def skinning(verts, weights, bind2world):
    deformed = np.zeros_like(verts)
    for i, v in enumerate(verts):
        v_org = np.ones(4)
        v_org[:3] = v
        v_updated = np.array([0.0, 0.0, 0.0, 1.0])
        for j in range(len(bind2world)):
            v_updated = v_updated + ((weights[i][j] * bind2world[j]) @ v_org)
        deformed[i] = v_updated[:3]
    return deformed


# https://blender.stackexchange.com/questions/44637/how-can-i-manually-calculate-bpy-types-posebone-matrix-using-blenders-python-ap/44975#44975
# def matrix_world(armature_ob, bone_name):
#     local = armature_ob.data.bones[bone_name].matrix_local
#     basis = armature_ob.pose.bones[bone_name].matrix_basis

#     parent = armature_ob.pose.bones[bone_name].parent
#     if parent == None:
#         return local @ basis
#     else:
#         parent_local = armature_ob.data.bones[parent.name].matrix_local
#         return matrix_world(armature_ob, parent.name) @ (parent_local.inverted() @ local) @ basis


def matrix_world(binds, basises, num):
    local = binds[num]
    basis = basises[num]

    if num < 1:
        return local @ basis

    parent_local = binds[num - 1]
    return matrix_world(binds, basises, num -
                        1) @ (np.linalg.inv(parent_local) @ local) @ basis


if __name__ == '__main__':

    # Export "Cylinder.001" in pose mode as "cylinder_gt.obj" and "Cylinder" as "cylinder_rest.obj"
    # Set Foward: Y Foward & Up: Z Up, to keep blender coordinate
    # and check "Keep Vertex Order" as well.

    # Then, "blender"  -b 20230402.blend  --python bpy_export.py" to export bone information as json

    with open('bones.json', 'r') as fp:
        bones = json.load(fp)

    with open('bone_weights.json', 'r') as fp:
        bone_weights = json.load(fp)

    keys = bones.keys()

    bind, inv_bind, trans = [], [], []
    for k in keys:
        inv_bind.append(np.array(bones[k]['inv_bind']))
        bind.append(np.linalg.inv(inv_bind[-1]))
        trans.append(np.array(bones[k]['matrix_basis']))

    bind2world = np.zeros((3, 4, 4))

    pose_bone_matices = []
    for i, k in enumerate(keys):
        pose_bone_matices.append(matrix_world(bind, trans, i))
    for i, k in enumerate(keys):
        bind2world[i] = pose_bone_matices[i] @ np.array(bones[k]['inv_bind'])

    rest = obj_io.loadObj('cylinder_rest.obj')
    weights = np.zeros((len(rest.verts), len(bind2world)))

    for j, k in enumerate(keys):
        for vid, w in bone_weights[k]:
            weights[vid][j] = w

    norm = np.sum(weights, axis=1)
    norm[norm <= 0] = 1.0
    weights /= norm[..., None]

    deformed_verts = skinning(rest.verts, weights, bind2world)

    rest.verts = deformed_verts
    obj_io.saveObj('cylinder_pose.obj', rest)
