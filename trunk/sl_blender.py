#!BPY

# """
# Name: 'Second Life Avatar'
# Blender: 243
# Group: 'AddMesh'
# Tooltip: 'Generate an armature for SL compatible animations'
# """

# from Blender import Draw, BGL
# 
# mystring = ""
# mymsg = ""
# toggle = 0

# def event(evt, val):    # the function to handle input events
#   global mystring, mymsg
# 
#   if not val:  # val = 0: it's a key/mbutton release
#     if evt in [Draw.LEFTMOUSE, Draw.MIDDLEMOUSE, Draw.RIGHTMOUSE]:
#       mymsg = "You released a mouse button."
#       Draw.Redraw(1)
#     return
# 
#   if evt == Draw.ESCKEY:
#     Draw.Exit()                 # exit when user presses ESC
#     return
# 
#   elif Draw.AKEY <= evt <= Draw.ZKEY: mystring += chr(evt)
#   elif evt == Draw.SPACEKEY: mystring += ' '
#   elif evt == Draw.BACKSPACEKEY and len(mystring):
#     mystring = mystring[:-1]
#   else: return # no need to redraw if nothing changed
# 
#   Draw.Redraw(1)
# 
# def button_event(evt):  # the function to handle Draw Button events
#   global mymsg, toggle
#   if evt == 1:
#     mymsg = "You pressed the toggle button."
#     toggle = 1 - toggle
#     Draw.Redraw(1)
# 
# def gui():              # the function to draw the screen
#   global mystring, mymsg, toggle
#   if len(mystring) > 90: mystring = ""
#   BGL.glClearColor(0,0,1,1)
#   BGL.glClear(BGL.GL_COLOR_BUFFER_BIT)
#   BGL.glColor3f(1,1,1)
#   Draw.Toggle("Toggle", 1, 10, 10, 55, 20, toggle,"A toggle button")
#   BGL.glRasterPos2i(72, 16)
#   if toggle: toggle_state = "down"
#   else: toggle_state = "up"
#   Draw.Text("The toggle button is %s." % toggle_state, "small")
#   BGL.glRasterPos2i(10, 230)
#   Draw.Text("Type letters from a to z, ESC to leave.")
#   BGL.glRasterPos2i(20, 200)
#   Draw.Text(mystring)
#   BGL.glColor3f(1,0.4,0.3)
#   BGL.glRasterPos2i(340, 70)
#   Draw.Text(mymsg, "tiny")
# 
# Draw.Register(gui, event, button_event)  # registering the 3 callbacks

import Blender
from Blender import Registry, Window, Mathutils

import xml.sax, struct, os.path

def sl_path_selected(filename):
    print "You chose the directory:", filename
    global regdict
    regdict = {'sl_directory': filename, 'params': {}}
    start()

# ######################################################################
# 
# class SkeletonHandler(xml.sax.ContentHandler):
#     def __init__(self, armature):
#         self.armature = armature
#         self.bone_stack = []
#     def startElement(self, name, attrs):
#         if name == 'bone':
#             bone = Armature.Editbone()
#             bone.name = attrs['name']
#             if self.bone_stack:
#                 bone.tail = self.bone_stack[-1].head
#             else:
#                 bone.tail = Mathutils.Vector(0,0,0)
#             print type(bone)
#             self.armature.bones[attrs['name']] = bone
#             if self.bone_stack:
#                 bone.parent = self.bone_stack[-1]
#             self.bone_stack.append(bone)
#     def endElement(self, name):
#         if name == 'bone':
#             self.bone_stack.pop()
# 
# def build_armature():
#     obj = Blender.Object.New('Armature', 'AvatarSkeleton')
#     armature = Armature.New('Avatar')
#     obj.link(armature)
#     scene = Blender.Scene.GetCurrent()
#     scene.objects.link(obj)
#     armature.makeEditable()
# 
#     sh = SkeletonHandler(armature)
#     parser = xml.sax.make_parser()
#     parser.setContentHandler(sh)
#     parser.parse(file(os.path.join(regdict['sl_directory'],
#                                    'character',
#                                    'avatar_skeleton.xml')))
#     sh.armature.update()
#     print "build_armature done!"
#     scene.update(0)

######################################################################

class AvatarBuilder(object):
    def __init__(self):
        self.scene = Blender.Scene.GetCurrent()

        editmode = Blender.Window.EditMode()
        if editmode: Blender.Window.EditMode(0)
        self.new_objects = []

        ah = self.LindenAvatarHandler(self)
        parser = xml.sax.make_parser()
        parser.setContentHandler(ah)
        parser.parse(file(os.path.join(regdict['sl_directory'],
                                       'character',
                                       'avatar_lad.xml')))

        self.eye_left_mesh.setLocation(*self.eye_left_location)
        self.eye_right_mesh.setLocation(*self.eye_right_location)
        self.avatar_object = Blender.Object.New('Empty', 'Avatar')
        self.scene.objects.link(self.avatar_object)
        self.avatar_object.makeParent(self.new_objects)
        self.new_objects.append(self.avatar_object)

        sorted_params = regdict['params'].items()
        sorted_params.sort()
        for k, v in sorted_params:
            self.avatar_object.addProperty('SL%d' % (k), v['default'])

        self.scene.objects.selected = self.new_objects
        self.scene.objects.active = self.avatar_object

        if editmode: Blender.Window.EditMode(1)
        Blender.Redraw()

    def build_mesh(self, from_file_name, type_name):
        obj = Blender.Object.New('Mesh', type_name)
        mesh = Blender.Mesh.New(type_name)
        obj.link(mesh)
        self.scene.objects.link(obj)
        self.new_objects.append(obj)
        if type_name == 'eyeBallLeftMesh':
            self.eye_left_mesh = obj
        elif type_name == 'eyeBallRightMesh':
            self.eye_right_mesh = obj

        llm_file = file(os.path.join(regdict['sl_directory'],
                                     'character',
                                     from_file_name))
        header = llm_file.read(24+1+1+12+12+1+12+2)
        header_fields = struct.unpack('<24sBBffffffBfffH', header)
        assert header_fields[0] == "Linden Binary Mesh 1.0\x00\x00"
        has_weights = header_fields[1]
        assert header_fields[2] == 0    # hasDetailTexCoords
        #obj.setLocation(*header_fields[3:6])
        assert header_fields[6] == 0.0  # rotation
        assert header_fields[7] == 0.0
        assert header_fields[8] == 0.0
        assert header_fields[9] == 0    # rotationOrder
        assert header_fields[10] == 1.0 # scale
        assert header_fields[11] == 1.0
        assert header_fields[12] == 1.0
        n_vertices = header_fields[13]

        def identity(n):
            return n
        def vector(list):
            return Mathutils.Vector(*list)
        def read_atom(type):
            size = struct.calcsize(type)
            return struct.unpack(type, llm_file.read(size))[0]
        def read_string(length):
            raw = read_atom('%ds' % (length))
            return raw[0:raw.index("\0")]
        def read_vector(vector_length, type):
            size = struct.calcsize(type) * vector_length
            struct.unpack(('%d' + type) % (vector_length),
                          llm_file.read(size))
        def read_vectors(n_vectors, vector_length, type, vector_fn = identity):
            size = struct.calcsize(type) * vector_length * n_vectors
            flat_list = struct.unpack(('%d' + type) % (vector_length * n_vectors),
                                      llm_file.read(size))
            return [vector_fn([flat_list[n * vector_length + i] for i in xrange(vector_length)]) for n in xrange(n_vectors)]

        base_coords = read_vectors(n_vertices, 3, 'f')
        mesh.verts.extend(base_coords)
        base_normals = read_vectors(n_vertices, 3, 'f', vector)
        for n, vertex in enumerate(mesh.verts):
            vertex.no = base_normals[n]
        base_binormals = read_vectors(n_vertices, 3, 'f')
        base_texcoords = read_vectors(n_vertices, 2, 'f', vector)
        if has_weights:
            weights = read_vector(n_vertices, 'f')

        n_faces = read_atom('H')
        faces = read_vectors(n_faces, 3, 'h')
        mesh.faces.extend(faces)
        mesh.faceUV = True
        for n, face in enumerate(mesh.faces):
            face.uv = [base_texcoords[i] for i in faces[n]]
            face.smooth = True

        if has_weights:
            n_skin_joints = read_atom('h')
            skin_joint_names = [read_string(64) for n in xrange(n_skin_joints)]
        else:
            skin_joint_names = []
        morphs = []
        while True:
            name = read_string(64)
            if name == 'End Morphs':
                break
            morphs.append([name])
            n_morph_vertices = read_atom('I')
            llm_file.read((4+12+12+12+8) * n_morph_vertices)
        remaps_str = llm_file.read(4)
        if remaps_str:
            n_remaps = struct.unpack('i', remaps_str)[0]
            remaps = read_vectors(n_remaps, 2, 'i')

        # print skin_joint_names
        # print morphs

    class LindenAvatarHandler(xml.sax.ContentHandler):
        def __init__(self, parent):
            self.parent = parent
        def startElement(self, name, attrs):
            if name == 'mesh' and attrs['lod'] == '0':
                self.parent.build_mesh(attrs['file_name'], attrs['type'])
            elif name == 'skeleton':
                self.parent.build_skeleton(attrs['file_name'])
            elif name == 'param':
                if attrs.has_key('value_min'):
                    value_min = float(attrs['value_min'])
                else:
                    value_min = 0.0
                if attrs.has_key('value_max'):
                    value_max = float(attrs['value_max'])
                else:
                    value_max = 1.0
                if attrs.has_key('value_default'):
                    value_default = float(attrs['value_default'])
                else:
                    value_default = 0.0
                    
                regdict['params'][int(attrs['id'])] = {'min': value_min,
                                                       'max': value_max,
                                                       'default': value_default}
                if attrs.has_key('wearable'):
                    if attrs.has_key('edit_group'):
                        print "%s/%s/%s" % (attrs['wearable'],
                                            attrs['edit_group'],
                                            attrs['name'])
                    else:
                        print "%s/%s" % (attrs['wearable'],
                                         attrs['name'])
                else:
                    pass #print attrs['id'], attrs['name']

        def endElement(self, name):
            pass

    def build_skeleton(self, from_file_name):
        sh = self.SkeletonHandler(self)
        parser = xml.sax.make_parser()
        parser.setContentHandler(sh)
        parser.parse(file(os.path.join(regdict['sl_directory'],
                                       'character',
                                       from_file_name)))

    class SkeletonHandler(xml.sax.ContentHandler):
        def __init__(self, parent):
            self.parent = parent
            self.bone_stack = []
        def startElement(self, name, attrs):
            if name == 'bone':
                bone = {}
                bone['name'] = attrs['name']
                testbone = Blender.Object.New('Empty', 'TestBone' + bone['name'])
                testbone.drawSize = 0.1
                self.parent.scene.objects.link(testbone)
                self.parent.new_objects.append(testbone)
                bone['location'] = [float(n) for n in attrs['pos'].split()]
                if self.bone_stack:
                    bone['location'] = [a + b for a, b in zip(bone['location'],
                                                              self.bone_stack[-1]['location'])]
                testbone.setLocation(*bone['location'])
                if bone['name'] == 'mEyeLeft':
                    self.parent.eye_left_location = bone['location']
                elif bone['name'] == 'mEyeRight':
                    self.parent.eye_right_location = bone['location']
                #self.armature.bones[attrs['name']] = bone
                #if self.bone_stack:
                #    bone.parent = self.bone_stack[-1]
                self.bone_stack.append(bone)
        def endElement(self, name):
            if name == 'bone':
                self.bone_stack.pop()

######################################################################

def start():
    if not regdict.has_key('params'):
        regdict['params'] = {}
    #build_armature()
    AvatarBuilder()
    Registry.SetKey('sl_blender', regdict, True)

regdict = Registry.GetKey('sl_blender', True)

if not regdict:
    Window.FileSelector(sl_path_selected, "SL viewer dir")
else:
    start()
