# vim:ts=4:et
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import sys
import os

import bpy
from mathutils import Vector,Matrix,Quaternion

from .cfgnode import ConfigNode, ConfigNodeError
from .import_mu import import_mu

def collect_objects(name, obj):
    def add_to_collection(collection, obj):
        collection.objects.link (obj)
        for child in obj.children:
            add_to_collection(collection, child)
    collection = bpy.data.collections.new(name)
    add_to_collection(collection, obj)
    return collection

def compile_model(db, path, type, name, cfg, scene):
    nodes = cfg.GetNodes("MODEL")
    if nodes:
        root = bpy.data.objects.new(name+":model", None)
        scene.collection.objects.link(root)
        for n in nodes:
            model = n.GetValue("model")
            position = Vector((0, 0, 0))
            rotation = Vector((0, 0, 0))
            scale = Vector((1, 1, 1))
            if n.HasValue("position"):
                position = parse_vector(n.GetValue("position"))
            if n.HasValue("rotation"):
                rotation = parse_vector(n.GetValue("rotation"))
            if n.HasValue("scale"):
                scale = parse_vector(n.GetValue("scale"))
            mdl = db.model(model)
            obj = mdl.instantiate(name+":submodel", position, rotation, scale)
            scene.collection.objects.link(obj)
            obj.parent = root
    else:
        mesh = db.model_by_path[path][0]
        url = os.path.join(path, mesh)
        model = db.model(url)
        position = Vector((0, 0, 0))
        rotation = Vector((0, 0, 0))
        scale = Vector((1, 1, 1))
        root = model.instantiate(name+":model", position, rotation, scale)
        scene.collection.objects.link(root)
    collection = collect_objects(type + ":" + name, root)
    collection.mumodelprops.name = name
    collection.mumodelprops.type = type
    return collection

def loaded_models_collection():
    if "loaded_models" not in bpy.data.collections:
        return bpy.data.collections.new("loaded_models")
    return bpy.data.collections["loaded_models"]

def instantiate_model(model, name, loc, rot, scale):
    obj = bpy.data.objects.new(name, None)
    obj.dupli_type='COLLECTION'
    obj.dupli_group=model
    obj.location = loc
    obj.scale = scale
    if type(rot) == Vector:
        # blender is right-handed, KSP is left-handed
        # FIXME: it might be better to convert the given euler rotation
        # to a quaternion (for consistency)
        # this assumes the rot vector came straight from a ksp cfg file
        obj.rotation_mode = 'XZY'
        obj.rotation_euler = -rot
    else:
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = rot
    return obj

class Model:
    @classmethod
    def Preloaded(cls):
        preloaded = {}
        for g in bpy.data.collections:
            if g.name[:6] == "model:":
                url = g.name[6:]
                preloaded[url] = Model(None, url)
        return preloaded
    def __init__(self, path, url):
        collectionname = "model:" + url
        if collectionname in bpy.data.collections:
            collection = bpy.data.collections["model:" + url]
        else:
            collection = loaded_models_collection()
            obj = import_mu(collection, path, False)
            obj.location = Vector((0, 0, 0))
            obj.rotation_quaternion = Quaternion((1,0,0,0))
            obj.scale = Vector((1,1,1))
            collection = collect_objects("model:" + url, obj)
        self.model = collection
    def instantiate(self, name, loc, rot, scale):
        return instantiate_model(self.model, name, loc, rot, scale)
