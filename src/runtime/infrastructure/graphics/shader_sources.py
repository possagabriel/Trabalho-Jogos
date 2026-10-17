"""Fontes GLSL do acabamento comic, isoladas do ciclo de vida OpenGL."""

VERTEX_SHADER_330 = """
#version 330 core
layout(location = 0) in vec2 posicao;
layout(location = 1) in vec2 uv;
out vec2 coordenada_uv;
void main() {
    gl_Position = vec4(posicao, 0.0, 1.0);
    coordenada_uv = uv;
}
"""

VERTEX_SHADER = """
#version 120
varying vec2 coordenada_uv;
void main() {
    gl_Position = ftransform();
    coordenada_uv = gl_MultiTexCoord0.xy;
}
"""

_FRAGMENT_TEMPLATE = """
{version}
uniform sampler2D quadro;
uniform vec2 resolucao;
uniform float intensidade;
uniform float qualidade;
uniform float forca_contorno;
uniform float tons;
uniform int usar_hachuras;
uniform float forca_grao;
uniform float saturacao;
{varying}
{output}

float luminancia(vec3 cor) {{
    return dot(cor, vec3(0.2126, 0.7152, 0.0722));
}}

float ruido(vec2 posicao) {{
    return fract(sin(dot(floor(posicao), vec2(12.9898, 78.233))) * 43758.5453);
}}

float linha_hachura(float valor, float periodo) {{
    float distancia = abs(mod(valor, periodo) - periodo * 0.5);
    return 1.0 - smoothstep(0.35, 1.15, distancia);
}}

void main() {{
    vec4 original = {texture_fn}(quadro, coordenada_uv);
    float forca = clamp(intensidade, 0.0, 1.0);
    if (forca < 0.005) {{
        {output_name} = original;
        return;
    }}

    vec3 cor = original.rgb;
    float luz_original = luminancia(cor);
    cor = mix(vec3(luz_original), cor, clamp(saturacao, 0.5, 1.5));
    cor = (cor - 0.5) * (1.0 + 0.18 * forca) + 0.5;

    // Quantiza a luz, nao cada canal RGB. Assim as faixas preservam o matiz.
    float luz = luminancia(max(cor, vec3(0.0)));
    float faixas = max(2.0, tons);
    float luz_posterizada = floor(luz * (faixas - 1.0) + 0.5) /
                            (faixas - 1.0);
    vec3 posterizada = clamp(cor * (luz_posterizada / max(luz, 0.04)),
                             0.0, 1.0);
    cor = mix(cor, posterizada, 0.68 * forca);

    float borda = 0.0;
    if (qualidade > 0.25 && forca_contorno > 0.005) {{
        vec2 pixel = 1.0 / resolucao;
        float tl = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(-1.0, -1.0)).rgb);
        float tc = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(0.0, -1.0)).rgb);
        float tr = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(1.0, -1.0)).rgb);
        float ml = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(-1.0, 0.0)).rgb);
        float mr = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(1.0, 0.0)).rgb);
        float bl = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(-1.0, 1.0)).rgb);
        float bc = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(0.0, 1.0)).rgb);
        float br = luminancia({texture_fn}(
            quadro, coordenada_uv + pixel * vec2(1.0, 1.0)).rgb);
        float sobel_x = -tl - 2.0 * ml - bl + tr + 2.0 * mr + br;
        float sobel_y = -tl - 2.0 * tc - tr + bl + 2.0 * bc + br;
        float magnitude = length(vec2(sobel_x, sobel_y));
        float inicio = mix(0.34, 0.12, clamp(forca_contorno, 0.0, 1.0));
        borda = smoothstep(inicio, inicio + 0.24, magnitude);
    }}

    // Coordenadas logicas mantem o padrao estavel em qualquer resolucao.
    vec2 posicao_logica = coordenada_uv * resolucao;
    if (qualidade > 0.25 && usar_hachuras == 1) {{
        float sombra = 1.0 - smoothstep(0.14, 0.58, luz_original);
        float hachura = linha_hachura(
            posicao_logica.x + posicao_logica.y, 9.0) * sombra;
        if (qualidade > 0.75) {{
            hachura += linha_hachura(
                posicao_logica.x - posicao_logica.y, 13.0) *
                smoothstep(0.55, 0.9, sombra);
        }}
        cor *= 1.0 - hachura * 0.11 * forca;
    }}

    float grao = ruido(posicao_logica) - 0.5;
    cor += grao * 0.035 * clamp(forca_grao, 0.0, 1.0) * forca;
    cor = mix(cor, vec3(0.018, 0.012, 0.026),
              borda * 0.82 * forca * clamp(forca_contorno, 0.0, 1.0));
    {output_name} = vec4(clamp(cor, 0.0, 1.0), original.a);
}}
"""

FRAGMENT_SHADER_330 = _FRAGMENT_TEMPLATE.format(
    version="#version 330 core",
    varying="in vec2 coordenada_uv;",
    output="out vec4 cor_saida;",
    texture_fn="texture",
    output_name="cor_saida",
)

FRAGMENT_SHADER = _FRAGMENT_TEMPLATE.format(
    version="#version 120",
    varying="varying vec2 coordenada_uv;",
    output="",
    texture_fn="texture2D",
    output_name="gl_FragColor",
)

__all__ = [
    "FRAGMENT_SHADER",
    "FRAGMENT_SHADER_330",
    "VERTEX_SHADER",
    "VERTEX_SHADER_330",
]
