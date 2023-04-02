import bpy
import json
import mathutils
import os

# https://blender.stackexchange.com/questions/44637/how-can-i-manually-calculate-bpy-types-posebone-matrix-using-blenders-python-ap/44975#44975


def matrix_world(armature_ob, bone_name):
    local = armature_ob.data.bones[bone_name].matrix_local
    basis = armature_ob.pose.bones[bone_name].matrix_basis

    parent = armature_ob.pose.bones[bone_name].parent
    if parent == None:
        return local @ basis
    else:
        parent_local = armature_ob.data.bones[parent.name].matrix_local
        return matrix_world(armature_ob, parent.name) @ (parent_local.inverted() @ local) @ basis


arm1 = bpy.data.objects['Armature.001']
bpy.context.view_layer.objects.active = arm1
arm1.data.pose_position = 'POSE'


# Write hierarchy, names, bind matrices for bones:
bones = {}
prev = mathutils.Matrix.Identity(4)
bone_names = [bone.name for bone in arm1.data.bones]

for name in bone_names:
    #name = bone.name
    bone = arm1.data.bones[name]
    bones[name] = {}
    bpy.ops.object.mode_set(mode='EDIT')
    transform = bone.matrix_local.copy()  # 4x4 bone matrix relative to armature
    # print(transform)
    transform.invert()
    # print(transform)
    # print()
    bones[name]['inv_bind'] = [list(t[:]) for t in transform]

    bpy.ops.object.mode_set(mode='POSE')
    pose_bone = arm1.pose.bones[name]
    print(name)
    print(bone.matrix)  # world-to-bone matrix, without parent
    print(pose_bone.matrix_basis)  # Transformaiton of bone itself
    # Considering parents, == pose_bone.matrix if rest mode
    print(bone.matrix_local)
    # Considering parents and their pose, == bone.matrix_local if reset mode
    print(pose_bone.matrix)

    print(matrix_world(arm1, name))  # == pose_bone.matrix

    if False:
        prev_inv = prev.copy()
        prev_inv.invert()
        print(pose_bone.matrix_basis @ prev_inv @ bone.matrix.to_4x4())
        prev = bone.matrix.to_4x4()

    if pose_bone.parent:
        print(name, 'has parent')
        to_parent = pose_bone.parent.matrix.copy()
        # print(to_parent)
        to_parent.invert()
        local_to_parent = to_parent @ pose_bone.matrix
        #local_to_parent = to_parent * pose_bone.matrix
        # print('---')
        #print(to_parent * pose_bone.matrix)
        #print(to_parent @ pose_bone.matrix)
        # print('---')
    else:
        local_to_parent = pose_bone.matrix

    t, r, s = local_to_parent.decompose()
    print()

    #tmp = mathutils.Matrix.LocRotScale(t, r, s)
    # print(tmp,'->',local_to_parent)

    bones[name]['location'] = list(pose_bone.location[:])
    bones[name]['rotation_quaternion'] = list(
        pose_bone.rotation_quaternion[:])
    bones[name]['scale'] = list(pose_bone.scale[:])
    bones[name]['matrix_basis'] = [
        list(t[:]) for t in pose_bone.matrix_basis]
    #bones[name]['matrix_basis'] = [list(t[:]) for t in pose_bone.matrix_basis]

    bones[name]['t'] = list(t[:])
    bones[name]['r'] = list(r[:])
    bones[name]['s'] = list(s[:])
    bones[name]['local_to_parent'] = [list(t[:]) for t in local_to_parent]

bone_weights = {}
str2id = {}
id2str = {}
obj1 = bpy.data.objects['Cylinder.001']
for k, v in bones.items():
    bone_weights[k] = []
    gidx = obj1.vertex_groups[k].index
    str2id[k] = gidx
    id2str[gidx] = k

print(id2str)

for v in obj1.data.vertices:
    for g in v.groups:
        bone_weights[id2str[g.group]].append([v.index, g.weight])

with open(os.path.join(os.getcwd(), 'bones.json'), 'w') as fp:
    json.dump(bones, fp, indent=4)

with open(os.path.join(os.getcwd(), 'bone_weights.json'), 'w') as fp:
    json.dump(bone_weights, fp, indent=4)
