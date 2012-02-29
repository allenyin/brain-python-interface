import numpy as np
from OpenGL.GL import *

from render import Renderer
from models import Texture

fbotypes = dict(
    depth=(GL_DEPTH_COMPONENT, GL_DEPTH_COMPONENT, GL_FLOAT, GL_DEPTH_ATTACHMENT), 
    stencil=(GL_DEPTH_COMPONENT, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, GL_STENCIL_ATTACHMENT), 
    colors=(GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE, GL_COLOR_ATTACHMENT0)
)

class FBO(object):
    def __init__(self, attachments, size, ncolors=1):
        self.colors = []
        self.types = []

        fbo = glGenFramebuffers(1)
        #Bind the texture to the renderer's framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)

        if "colors" in attachments:
            for i in range(ncolors):
                tex = Texture(None, size=size)
                tex.init()
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, tex.tex, 0)
                self.colors.append(tex)
                self.types.append(GL_COLOR_ATTACHMENT0+i)
            attachments.remove("colors")
        
        for kind in attachments:
            texform, textype, dtype, fbtype = fbotypes[kind]
            tex = Texture(None, size=size, iformat=texform, exformat=textype, dtype=dtype)
            tex.init()
            glFramebufferTexture2D(GL_FRAMEBUFFER, fbtype, GL_TEXTURE_2D, tex.tex, 0)
            self.types.append(fbtype)
        
        #We always need a depth buffer! Otherwise occlusion will be messed up
        if "depth" not in attachments:
            rb = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, rb)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, size[0], size[1])
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rb)
            #self.types.append(GL_DEPTH_ATTACHMENT)
        
        self.fbo = fbo
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

class FBOrender(Renderer):
    def __init__(self, fbo, *args, **kwargs):
        super(FBOrender, self).__init__(*args, **kwargs)
        self.fbo = fbo

    def draw_fsquad(self, shader, **kwargs):
        ctx = self.programs[shader]
        glUseProgram(ctx.program)
        for name, arg in kwargs.items():
            ctx.uniforms[name] = arg
        
        glEnableVertexAttribArray(ctx.attributes['position'])
        glBindBuffer(GL_ARRAY_BUFFER, self.fsquad_buf[0])
        glVertexAttribPointer(ctx.attributes['position'],
            4, GL_FLOAT, GL_FALSE, 4*4, GLvoidp(0))
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.fsquad_buf[1]);
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_SHORT, GLvoidp(0))
        glDisableVertexAttribArray(ctx.attributes['position'])

    def draw_to_fbo(self, root, **kwargs):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo.fbo)
        glDrawBuffers(self.fbo.types)
        #Erase old buffer info
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        super(FBOrender, self).draw(root, **kwargs)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    