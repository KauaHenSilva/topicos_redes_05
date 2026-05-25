def pixels_para_km(px_x: float, px_y: float, largura_canvas: int, altura_canvas: int, largura_km: float, altura_km: float) -> tuple[float, float]:
    """Converte coordenadas em pixels do canvas para quilômetros do ambiente da simulação."""
    if largura_canvas <= 1 or altura_canvas <= 1:
        return float(px_x), float(px_y)

    km_x = (px_x * largura_km) / largura_canvas
    km_y = (px_y * altura_km) / altura_canvas
    return round(km_x, 2), round(km_y, 2)


def km_para_pixels(km_x: float, km_y: float, largura_canvas: int, altura_canvas: int, largura_km: float, altura_km: float) -> tuple[float, float]:
    """Converte coordenadas em quilômetros da simulação para pixels do canvas."""
    if largura_km <= 0 or altura_km <= 0:
        return 0.0, 0.0
    
    px_x = (km_x * largura_canvas) / largura_km
    px_y = (km_y * altura_canvas) / altura_km
    return px_x, px_y


def raio_km_para_pixels(raio_km: float, largura_canvas: int, altura_canvas: int, largura_km: float, altura_km: float) -> tuple[float, float]:
    """Converte um raio (em km) para larguras/alturas em pixels (oval do canvas)."""
    if largura_km <= 0 or altura_km <= 0:
        return 0.0, 0.0

    return (
        abs((float(raio_km) * largura_canvas) / largura_km),
        abs((float(raio_km) * altura_canvas) / altura_km),
    )
