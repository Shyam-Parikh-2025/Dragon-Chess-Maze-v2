VERTEX_SHADER_3D = """
#version 330 core
in vec3 in_pos;
uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
void main() {
    gl_Position = m_proj * m_view * m_model * vec4(in_pos, 1.0);
}
"""
 
FRAGMENT_SHADER_3D = """
#version 330 core
uniform vec3 u_color;
out vec4 fragColor;
void main() {
    fragColor = vec4(u_color, 1.0);
}
"""