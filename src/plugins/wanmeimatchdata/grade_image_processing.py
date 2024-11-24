from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 创建渐变函数
def linear_gradient(start_color, end_color, progress):
    return tuple([int(start_color[i] + (end_color[i] - start_color[i]) * progress) for i in range(3)])

def draw_hexagon(draw, size, center, progress, start_color, end_color, fill_color, text, font_path):
    angle = np.pi / 3  # 60度
    start_angle = np.pi / 2  # 调整为90度旋转（顺时针旋转60度）
    radius = size / 2
    edge_gap = 60  # 六边形边缘和内框条之间的间隙

    # 计算六边形的6个顶点坐标
    vertices = [(center[0] + radius * np.cos(i * angle + start_angle), center[1] + radius * np.sin(i * angle + start_angle)) for i in range(6)]
    
    # 绘制六边形底色
    draw.polygon(vertices, fill=fill_color)
    
    # 绘制完整的内框条（颜色为#1d2431）


    edge_thickness = 50  # 调整内框条宽度
    progress_vertices_outer = [(center[0] + (radius - edge_gap) * np.cos(i * angle + start_angle), 
                                center[1] + (radius - edge_gap) * np.sin(i * angle + start_angle)) for i in range(6)]
    
    progress_vertices_inner = [(center[0] + (radius - edge_thickness - edge_gap) * np.cos(i * angle + start_angle), 
                                center[1] + (radius - edge_thickness - edge_gap) * np.sin(i * angle + start_angle)) for i in range(6)]


    remaining_color = (29, 36, 49)  # 设置为#1d2431颜色
    for i in range(6):
        points = [progress_vertices_outer[i], progress_vertices_outer[(i + 1) % 6],
                  progress_vertices_inner[(i + 1) % 6], progress_vertices_inner[i]]
        draw.polygon(points, fill=remaining_color)

    # 总共六条边
    total_edges = 6
    full_edges_to_draw = int(progress * total_edges)  # 完整绘制的边数
    remaining_progress = (progress * total_edges) - full_edges_to_draw  # 在下一条边上剩余的进度

    # 绘制完整的边（渐变效果）
    for i in range(full_edges_to_draw):
        # 每条边上绘制多个小梯形以实现连续渐变
        segments_per_edge = 100  # 每条边分成100个小段，增加分段数可使渐变更平滑
        for j in range(segments_per_edge):
            seg_progress = (i + j / segments_per_edge) / total_edges
            color = linear_gradient(start_color, end_color, seg_progress)

            # 每个小梯形的外顶点
            outer_start = progress_vertices_outer[i]
            outer_end = progress_vertices_outer[(i + 1) % 6]
            inner_start = progress_vertices_inner[i]
            inner_end = progress_vertices_inner[(i + 1) % 6]

            partial_outer = (
                outer_start[0] + (j / segments_per_edge) * (outer_end[0] - outer_start[0]),
                outer_start[1] + (j / segments_per_edge) * (outer_end[1] - outer_start[1])
            )
            partial_inner = (
                inner_start[0] + (j / segments_per_edge) * (inner_end[0] - inner_start[0]),
                inner_start[1] + (j / segments_per_edge) * (inner_end[1] - inner_start[1])
            )

            next_partial_outer = (
                outer_start[0] + ((j + 1) / segments_per_edge) * (outer_end[0] - outer_start[0]),
                outer_start[1] + ((j + 1) / segments_per_edge) * (outer_end[1] - outer_start[1])
            )
            next_partial_inner = (
                inner_start[0] + ((j + 1) / segments_per_edge) * (inner_end[0] - inner_start[0]),
                inner_start[1] + ((j + 1) / segments_per_edge) * (inner_end[1] - inner_start[1])
            )

            # 绘制小梯形
            points = [partial_outer, next_partial_outer, next_partial_inner, partial_inner]
            draw.polygon(points, fill=color)

    # 绘制未完成的那一条边的剩余进度
    if remaining_progress > 0 and full_edges_to_draw < total_edges:
        i = full_edges_to_draw
        segments_per_edge = 100
        segments_to_draw = int(segments_per_edge * remaining_progress)  # 根据剩余进度计算要绘制的小段数
        for j in range(segments_to_draw):
            seg_progress = (i + j / segments_per_edge) / total_edges
            color = linear_gradient(start_color, end_color, seg_progress)

            outer_start = progress_vertices_outer[i]
            outer_end = progress_vertices_outer[(i + 1) % 6]
            inner_start = progress_vertices_inner[i]
            inner_end = progress_vertices_inner[(i + 1) % 6]

            partial_outer = (
                outer_start[0] + (j / segments_per_edge) * (outer_end[0] - outer_start[0]),
                outer_start[1] + (j / segments_per_edge) * (outer_end[1] - outer_start[1])
            )
            partial_inner = (
                inner_start[0] + (j / segments_per_edge) * (inner_end[0] - inner_start[0]),
                inner_start[1] + (j / segments_per_edge) * (inner_end[1] - inner_start[1])
            )

            next_partial_outer = (
                outer_start[0] + ((j + 1) / segments_per_edge) * (outer_end[0] - outer_start[0]),
                outer_start[1] + ((j + 1) / segments_per_edge) * (outer_end[1] - outer_start[1])
            )
            next_partial_inner = (
                inner_start[0] + ((j + 1) / segments_per_edge) * (inner_end[0] - inner_start[0]),
                inner_start[1] + ((j + 1) / segments_per_edge) * (inner_end[1] - inner_start[1])
            )

            points = [partial_outer, next_partial_outer, next_partial_inner, partial_inner]
            draw.polygon(points, fill=color)

    # 绘制文本
    font = ImageFont.truetype(font_path, size=int(radius * 0.85))  # 调整字体大小
    text_color = (255, 255, 255)

    # 使用 getbbox 获取文本尺寸
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_position = (center[0] - text_width / 2, center[1] - text_height / 2 - 80 )
    draw.text(text_position, text, fill=text_color, font=font)

# 主函数
def create_hexagon_image(size, progress, text, font_path):
    # 生成高分辨率图像以实现抗锯齿效果
    scale_factor = 4  # 放大比例
    image = Image.new('RGBA', (size * scale_factor, size * scale_factor), (0, 0, 0, 0))  # 使用透明背景 (RGBA)
    draw = ImageDraw.Draw(image)
    
    # 参数定义
    center = (size * scale_factor // 2, size * scale_factor // 2)
    start_color = (98, 146, 222)
    end_color = (126, 252, 149)
    fill_color = (22, 23, 29)

    draw_hexagon(draw, size * scale_factor, center, progress, start_color, end_color, fill_color, text, font_path)

    # 缩小回原始大小并应用抗锯齿
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image

# 使用示例
##font_path = "C:\\Users\\27085\\Desktop\\新功能\\CS.ttf"  # 替换为实际字体路径
#image = create_hexagon_image(200, 0.1, 'C+', font_path)
#image.show()
