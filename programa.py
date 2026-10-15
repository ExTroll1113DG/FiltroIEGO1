#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stats de personajes por nivel + rankings por posicion.
Un solo archivo, sin dependencias externas (solo libreria estandar de Python 3.8+).

Uso:   python programa.py [archivo.7z | ie_a.fa]   (ventana grafica)  |  python programa.py --cli [archivo]  (texto)
Si no se indica archivo, lo pide por pantalla. Funciona con cualquier archivo del mismo
tipo (datos randomizados distintos).

Referencias: la opcion 4 contrasta una tabla (.xlsx, .ods, .csv o texto) con el
modelo real del juego y guarda solo correcciones de base compatibles en calibracion.json.
"""
import hashlib, json, lzma, math, os, struct, sys, tempfile, unicodedata, zlib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FICHERO_CALIB = AQUI / "calibracion.json"

# ----------------------------------------------------------------------------------
# Constantes y tablas del modelo del juego (ver RESEARCH.md)
# ----------------------------------------------------------------------------------
STATS = ["PE", "PT", "Tiro", "Regate", "Tecnica", "Defensa", "Rapidez", "Aguante", "Control", "Suerte"]
COL_STAT = {s: 2 + i for i, s in enumerate(STATS)}        # columnas de chara_param con la stat base
COL_CURVA = {s: 23 + i for i, s in enumerate(STATS)}     # columnas con el tipo de curva de cada stat
COL_ELEMENTO = 12
ELEMENTOS = {1: "Aire", 2: "Bosque", 3: "Fuego", 4: "Tierra"}
NIVEL_MIN, NIVEL_MAX = 1, 99

# Rutina GO Light 0x0033E404. Datos del ejecutable, no tasas ajustadas.
# Tablas 0x00586C18 y 0x00586DA8; ver RESEARCH.md.
COL_PERFIL = 21
MODELO = "go-light-arm-v1"
PERFILES = ((1.0, 1.0, 0.7, 1.0, 1.0, 0.9, 1.1, 1.1, 1.2, 1.0), (1.0, 1.0, 0.7, 0.9, 1.0, 1.0, 0.9, 1.2, 1.3, 1.0), (1.0, 1.0, 0.8, 0.9, 1.0, 1.3, 1.0, 1.3, 0.7, 1.0), (1.0, 1.0, 0.9, 1.0, 1.0, 1.1, 1.1, 1.2, 0.7, 1.0), (1.0, 1.0, 1.0, 1.3, 1.1, 0.9, 1.0, 1.0, 0.7, 1.0), (1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.1, 0.9, 0.7, 1.0), (1.0, 1.0, 1.0, 1.1, 1.0, 0.9, 1.2, 1.1, 0.7, 1.0), (1.0, 1.0, 1.3, 0.9, 1.0, 1.1, 0.9, 1.0, 0.7, 1.1), (1.0, 1.0, 1.0, 1.1, 1.0, 0.9, 1.1, 1.2, 0.7, 1.0), (1.0, 1.0, 1.1, 0.9, 1.0, 1.0, 1.2, 1.1, 0.7, 1.0))
FACTORES_ELEMENTO = ((1.0, 1.0, 2.0, 12.0, 12.0, 1.0, 12.0, 3.0, 4.0, 1.0), (1.0, 1.0, 1.0, 12.0, 1.0, 12.0, 12.0, 1.0, 1.0, 1.0), (1.0, 1.0, 12.0, 1.0, 12.0, 1.0, 12.0, 1.0, 1.0, 1.0), (1.0, 1.0, 2.0, 1.0, 2.0, 3.0, 1.0, 12.0, 12.0, 1.0))

POSICIONES = {
    "Delantero": {"Tiro": 4, "Rapidez": 2, "Regate": 1, "Tecnica": 1},
    "Medio":     {"Regate": 3, "Tecnica": 1, "Defensa": 1, "Rapidez": 1},
    "Defensa":   {"Defensa": 4, "Regate": 1, "Tecnica": 1, "Suerte": 1},
    "Portero":   {"Control": 5, "Aguante": 1, "Defensa": 1},
}

# ----------------------------------------------------------------------------------
# 1) Extraer .7z simple (un fichero, LZMA2) sin 7z ni librerias externas
# ----------------------------------------------------------------------------------
def extraer_7z(ruta_7z, ruta_out):
    f = open(ruta_7z, "rb")
    h = f.read(32)
    if h[:6] != b"7z\xbc\xaf\x27\x1c":
        raise ValueError("No es un archivo .7z")
    nho, nhs, _ = struct.unpack("<QQI", h[12:32])
    f.seek(32 + nho); hd = f.read(nhs)
    if hd[0] != 0x01:
        raise ValueError("Cabecera 7z comprimida: extrae el archivo a mano con 7-Zip y pasa el ie_a.fa")

    def num(b, i):
        first = b[i]; mask = 0x80; val = 0; n = 0
        while n < 8 and (first & mask):
            val |= b[i + 1 + n] << (8 * n); n += 1; mask >>= 1
        val |= (first & (mask - 1)) << (8 * n)
        return val, i + 1 + n

    i = hd.index(b"\x06") + 1
    packpos, i = num(hd, i); _, i = num(hd, i)
    i = hd.index(b"\x09", i) + 1
    packsize, i = num(hd, i)
    j = hd.index(b"\x0c", i) + 1
    unpack, j = num(hd, j)
    prop = hd[hd.index(b"\x21\x01", i) + 2]
    dict_size = (2 | (prop & 1)) << (prop // 2 + 11)
    f.seek(32 + packpos)
    dec = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "dict_size": dict_size}])
    resto = packsize; total = 0
    with open(ruta_out, "wb") as out:
        while resto > 0:
            b = f.read(min(1 << 20, resto)); resto -= len(b)
            d = dec.decompress(b); out.write(d); total += len(d)
    if total != unpack:
        raise ValueError("Extraccion incompleta")

# ----------------------------------------------------------------------------------
# 2) Compresion Level-5 (LZ10 / Huffman / RLE)
# ----------------------------------------------------------------------------------
def _lz10(data, size):
    out = bytearray(); i = 4; n = len(data)
    while len(out) < size and i < n:
        flags = data[i]; i += 1
        for b in range(8):
            if len(out) >= size: break
            if flags & (0x80 >> b):
                b0, b1 = data[i], data[i + 1]; i += 2
                ln = (b0 >> 4) + 3; disp = (((b0 & 0xF) << 8) | b1) + 1
                for _ in range(ln): out.append(out[-disp])
            else:
                out.append(data[i]); i += 1
    return bytes(out[:size])

def _huff(data, size, bits):
    tsz = (data[4] + 1) * 2
    table = data[4:4 + tsz]; pos = 4 + tsz
    total = size if bits == 8 else size * 2
    vals = []; node = 1
    while len(vals) < total:
        w = struct.unpack_from("<I", data, pos)[0]; pos += 4
        for k in range(31, -1, -1):
            bit = (w >> k) & 1
            nv = table[node]
            nxt = (node & ~1) + (nv & 0x3F) * 2 + 2 + bit
            if (nv & 0x40) if bit else (nv & 0x80):
                vals.append(table[nxt]); node = 1
                if len(vals) >= total: break
            else:
                node = nxt
    if bits == 8: return bytes(vals)
    return bytes(vals[i] | (vals[i + 1] << 4) for i in range(0, len(vals), 2))

def _rle(data, size):
    out = bytearray(); i = 4
    while len(out) < size:
        c = data[i]; i += 1
        if c & 0x80: out += bytes([data[i]]) * ((c & 0x7F) + 4); i += 1
        else: out += data[i:i + (c & 0x7F) + 1]; i += (c & 0x7F) + 1
    return bytes(out[:size])

def descomprimir(data):
    v = struct.unpack_from("<I", data, 0)[0]
    m, size = v & 7, v >> 3
    if m == 0: return data[4:4 + size]
    if m == 1: return _lz10(data, size)
    if m == 2: return _huff(data, size, 4)
    if m == 3: return _huff(data, size, 8)
    if m == 4: return _rle(data, size)
    raise ValueError("Metodo de compresion desconocido: %d" % m)

# ----------------------------------------------------------------------------------
# 3) Contenedor ARC0 y tablas CfgBin
# ----------------------------------------------------------------------------------
class Arc0:
    def __init__(self, ruta):
        self.f = open(ruta, "rb")
        h = self.f.read(0x48)
        if h[:4] != b"ARC0":
            raise ValueError("El archivo no es un contenedor ARC0 (ie_a.fa)")
        _, _, self.o_file, self.o_name, self.o_data = struct.unpack_from("<5I", h, 4)
        self.f.seek(self.o_file); fe = descomprimir(self.f.read(self.o_name - self.o_file))
        self.por_hash = {}
        for i in range(len(fe) // 16):
            hh, _, off, size = struct.unpack_from("<IIII", fe, i * 16)
            self.por_hash.setdefault(hh, []).append((off, size))

    def leer(self, nombre):
        h = zlib.crc32(nombre.encode()) & 0xFFFFFFFF
        if h not in self.por_hash:
            raise KeyError("No esta %s en el archivo" % nombre)
        off, size = self.por_hash[h][0]
        self.f.seek(self.o_data + off)
        return self.f.read(size)

def cfgbin(data):
    """Devuelve lista de (nombre_tabla, [params]) de un .cfg.bin"""
    n, ko, slen, _ = struct.unpack_from("<IIII", data, 0)
    kt = (ko + slen + 0xF) & ~0xF
    _, kcount, kstr, _ = struct.unpack_from("<IIII", data, kt)
    nombres = {}
    for i in range(kcount):
        h, off = struct.unpack_from("<II", data, kt + 16 + i * 8)
        nombres[h] = data[kt + kstr + off: kt + kstr + off + 128].split(b"\0")[0].decode("utf-8", "replace")
    strtab = data[ko: ko + slen]
    def cadena(off):
        if off >= len(strtab): return None
        return strtab[off: strtab.find(b"\0", off)].decode("utf-8", "replace")
    ents = []; p = 0x10
    for _ in range(n):
        h = struct.unpack_from("<I", data, p)[0]; cnt = data[p + 4]
        tb = (cnt + 3) // 4; tbytes = data[p + 5: p + 5 + tb]
        q = p + ((5 + tb + 3) & ~3)
        vals = []
        for k in range(cnt):
            t = (tbytes[k // 4] >> ((k % 4) * 2)) & 3
            raw = struct.unpack_from("<I", data, q)[0]; q += 4
            if t == 0: vals.append(cadena(raw))
            elif t == 2: vals.append(struct.unpack("<f", struct.pack("<I", raw))[0])
            else: vals.append(struct.unpack("<i", struct.pack("<I", raw))[0])
        ents.append((nombres.get(h, "#%08x" % h), vals))
        p = q
    return ents

# ----------------------------------------------------------------------------------
# 4) Base de datos de personajes
# ----------------------------------------------------------------------------------
def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return " ".join("".join(c for c in s if unicodedata.category(c) != "Mn").split())

def cargar_bd(ruta):
    ruta = Path(ruta.strip().strip('"'))
    if not ruta.exists():
        raise FileNotFoundError("No existe: %s" % ruta)
    if ruta.suffix.lower() == ".7z":
        tmp = Path(tempfile.gettempdir()) / (ruta.stem + "_extraido.fa")
        if not tmp.exists() or tmp.stat().st_mtime < ruta.stat().st_mtime:
            print("Extrayendo .7z (puede tardar un minuto)...")
            extraer_7z(str(ruta), str(tmp))
        ruta = tmp
    a = Arc0(str(ruta))
    P = [v for n, v in cfgbin(a.leer("chara_param.cfg.bin")) if n == "CHARA_PARAM_INFO"]
    B = {v[0]: v for n, v in cfgbin(a.leer("chara_base.cfg.bin")) if n == "CHARA_BASE_INFO"}
    nombres = {v[0]: v[5] for n, v in cfgbin(a.leer("chara_text_es.cfg.bin")) if n == "NOUN_INFO"}
    # Pasivas permanentes: se leen para contrastar referencias sin confundir
    # una habilidad aprendida con crecimiento natural. Las stats siguen sin bonus.
    pasivas = {}
    try:
        habilidades = {v[0]: v for n, v in cfgbin(a.leer("skill_config.cfg.bin"))
                       if n == "SKILL_CONFIG_INFO"}
        tipo_stat = {1: "Control", 2: "Defensa", 3: "Regate", 4: "Tiro", 5: "Rapidez",
                     6: "Suerte", 7: "Tecnica", 8: "Aguante", 9: "PT", 10: "PE"}
        for n, v in cfgbin(a.leer("skill_table.cfg.bin")):
            if n != "SKILL_TABLE": continue
            h = habilidades.get(v[2])
            if h and h[6] == 15 and h[9] == 1 and h[3] in tipo_stat and h[19] in (10, 20):
                pasivas[v[0]] = {"nivel": v[1], "stat": tipo_stat[h[3]],
                                  "bonus": h[19], "habilidad_id": v[2]}
    except KeyError:
        pass  # Los archivos de datos reducidos pueden carecer de tablas de skills.
    bd = []
    for r in P:
        b = B.get(r[1])
        if not b: continue
        nombre = nombres.get(b[2]) or "id%d" % r[1]
        bd.append({"nombre": nombre, "corto": nombres.get(b[3]) or nombre,
                   "elemento": ELEMENTOS.get(r[COL_ELEMENTO], "?"),
                   "elemento_id": r[COL_ELEMENTO], "perfil": r[COL_PERFIL], "param_id": r[0],
                   "clave": hashlib.sha256(json.dumps(r, ensure_ascii=False).encode()).hexdigest(),
                   "pasivas": [pasivas[i] for i in range(r[18], r[18] + r[17]) if i in pasivas],
                   "base": {s: r[COL_STAT[s]] for s in STATS},
                   "curva": {s: r[COL_CURVA[s]] for s in STATS}})
    a.f.close()
    return bd

# ----------------------------------------------------------------------------------
# 5) Modelo de crecimiento y calibracion
# ----------------------------------------------------------------------------------
def _f32(x):
    """Redondeo IEEE754 simple tras cada operación VFP (VFU no fusionada)."""
    return struct.unpack("<f", struct.pack("<f", x))[0]

def _mul(a, b): return _f32(_f32(a) * _f32(b))
def _add(a, b): return _f32(_f32(a) + _f32(b))
def _mla(a, b, c): return _add(a, _mul(b, c))

def stat_juego(base, curva, nivel, indice, elemento, perfil):
    """Stat natural: sin equipamiento, entrenamiento ni pasivas.

    Reproduce 0x0033E404 del ejecutable GO Light adjunto, operación a
    operación. El valor base del archivo NO es necesariamente la stat a nivel 1.
    """
    if not isinstance(nivel, int) or not NIVEL_MIN <= nivel <= NIVEL_MAX:
        raise ValueError("El nivel debe ser un entero entre 1 y 99")
    if not 0 <= indice < len(STATS):
        raise ValueError("Indice de stat invalido")
    if not 0 <= base <= 255:
        raise ValueError("La base del archivo debe estar entre 0 y 255")
    l = float(nivel)
    if curva in (7, 8, 9):
        cuadrado, lineal, offset = {
            7: (-0.014600000344216824, 2.783099889755249, 2.7685000896453857),
            8: (-0.00839999970048666, 1.8553999662399292, 1.847000002861023),
            9: (-0.008299999870359898, 1.5461000204086304, 1.5377999544143677),
        }[curva]
        total = _add(_mla(_mla(base, nivel * nivel, cuadrado), l, lineal), -offset)
    else:
        if not 1 <= elemento <= len(FACTORES_ELEMENTO):
            raise ValueError("Elemento invalido: %s" % elemento)
        if not 1 <= perfil <= len(PERFILES):
            raise ValueError("Perfil de crecimiento invalido: %s" % perfil)
        a = PERFILES[perfil - 1][indice]
        b = FACTORES_ELEMENTO[elemento - 1][indice]
        if curva == 3:
            t = _mla(l, l, 0.02)
            t = _mla(t, b, 0.25)
            tramo = _mul(_add(455, -_mul(l, 2)), 0.3030303120613098)
            t = _mul(_mul(_mul(t, tramo), 0.01315789483487606), 0.45)
        elif curva == 4:
            t = _mla(l, l, 0.02857142873108387)
            t = _mla(t, b, 0.5555555820465088)
            tramo = _mul(_add(250, -l), 0.3333333432674408)
            t = _mul(_mul(_mul(t, tramo), 0.016129031777381897), 0.55)
        elif curva in (5, 6):
            if curva == 5:
                factor, pendiente, escala, limite = 0.003448275849223137, 4.5, 0.65, 145
            else:
                factor, pendiente, escala, limite = 0.009523809887468815, 5.5, 0.55, 144
            t = _mul(b, _mul(l, factor))
            t = _mla(t, _mul(l, pendiente), 0.10526315867900848)
            t = _mul(_mul(t, escala), l)
            t = _f32(t / _add(limite, -l))
        else:  # curva 0, 1 y desconocidas: misma rama del juego
            factor, pendiente = (0.1666666716337204, 1.2) if curva == 2 else (0.0833333358168602, 0.9)
            t = _mul(b, _mul(l, factor))
            t = _mla(t, l, pendiente)
            t = _mla(_mul(t, 0.05), l, 0.5)
        total = _mla(base, t, a)
    return min(0xffffffff, max(0, int(total))) & 0xffff

def cargar_rates():
    # Se conserva el nombre para mantener la interfaz GUI/CLI existente.
    if FICHERO_CALIB.exists():
        try:
            with FICHERO_CALIB.open(encoding="utf-8") as f:
                datos = json.load(f)
            if datos.get("modelo") == MODELO:
                return datos
            print("Aviso: calibracion lineal antigua ignorada; vuelve a importar la tabla.")
        except (OSError, ValueError):
            print("Aviso: calibracion.json ilegible; se usa el modelo del juego.")
    return {"modelo": MODELO, "bases": {}}

def _descifrar_partida(datos):
    """Envoltura XORShift de Level-5. CRC del archivo cifrado antes de leerlo.

    Algoritmo documentado en StudioElevenLib/XORShift.cs y yw_save.py;
    las partidas exportadas desde Checkpoint conservan esta envoltura interna.
    """
    if len(datos) < 16:
        raise ValueError("Partida incompleta")
    crc, semilla = struct.unpack_from("<II", datos, len(datos) - 8)
    if zlib.crc32(datos[:-8]) & 0xffffffff != crc:
        raise ValueError("CRC de partida incorrecto; usa game.ie4 exportado con Checkpoint/JKSM")
    if struct.unpack_from("<H", datos, 4)[0] in (0x2cf1, 0x6cf1):
        return datos
    estado = []
    for i in range(3):
        semilla = ((semilla ^ (semilla >> 30)) * 0x6c078965 + i + 1) & 0xffffffff
        estado.append(semilla)
    estado.append(0x03df95b3)
    tabla = list(range(256))
    for _ in range(4096):
        x, y = estado[0], estado[3]
        x = (x ^ (x << 11)) & 0xffffffff
        x = (x ^ (x >> 8)) & 0xffffffff
        valor = x ^ (y ^ (y >> 19))
        estado = estado[1:] + [valor]
        a, b = tabla[valor & 255], tabla[(valor >> 8) & 255]
        tabla[a], tabla[b] = tabla[b], tabla[a]
    primos = []; n = 3
    while len(primos) < 256:
        if all(n % d for d in range(2, math.isqrt(n) + 1)): primos.append(n)
        n += 2
    salida = bytearray(datos)
    for i in range(len(datos) - 8):
        primo = primos[tabla[(i & 0xff00) >> 8]]
        salida[i] ^= tabla[(primo * (i + 1)) & 255]
    if struct.unpack_from("<H", salida, 4)[0] not in (0x2cf1, 0x6cf1):
        raise ValueError("No es una partida de Inazuma Eleven GO (game.ie4)")
    return bytes(salida)

def leer_partida(ruta):
    """Solo lectura: devuelve registros de jugadores, sin nombres personales."""
    raw = Path(ruta).read_bytes()
    datos = _descifrar_partida(raw)
    inicio = 0x3438 if struct.unpack_from("<H", datos, 4)[0] == 0x6cf1 else 0x3488
    if len(datos) < inicio + 112 * 204:
        raise ValueError("Tabla de jugadores incompleta")
    jugadores = []
    for slot in range(112):
        off = inicio + slot * 204
        indice, ident, experiencia = struct.unpack_from("<IiI", datos, off)
        if not ident: continue
        nivel = datos[off + 18]
        if not NIVEL_MIN <= nivel <= NIVEL_MAX:
            raise ValueError("Registro de partida invalido en slot %d" % slot)
        jugadores.append({"indice": indice, "param_id": ident, "nivel": nivel,
            "experiencia": experiencia,
            "entrenamiento": dict(zip(STATS[2:], struct.unpack_from("<8h", datos, off + 32))),
            "equipo_indices": list(struct.unpack_from("<4I", datos, off + 56))})
    return jugadores, hashlib.sha256(raw).hexdigest()

def importar_entrenamiento(bd, ruta, rates=None):
    registros, huella = leer_partida(ruta)
    resultado = dict(rates or {"modelo": MODELO, "bases": {}})
    resultado["bases"] = dict(resultado.get("bases", {}))
    resultado["entrenamiento"] = dict(resultado.get("entrenamiento", {}))
    por_id = {}
    for registro in registros:
        ident = registro["param_id"]
        if ident in por_id and registro["entrenamiento"] != por_id[ident]["entrenamiento"]:
            raise ValueError("La partida contiene varios ejemplares con distinto entrenamiento para ID %s" % ident)
        por_id[ident] = registro
    vistos = set(); equipo = []
    for personaje in bd:
        resultado["entrenamiento"].pop(personaje["clave"], None)
        ident = personaje.get("param_id")
        if ident not in por_id: continue
        if ident in vistos: raise ValueError("ID de personaje duplicado en los datos")
        vistos.add(ident)
        registro = por_id[ident]; clave = personaje["clave"]
        # Al cambiar la fuente de estado, retirar calibraciones de estos jugadores:
        # no sumar dos veces entrenamiento previamente confundido con una base.
        resultado["bases"].pop(clave, None)
        bonus = {s: v for s, v in registro["entrenamiento"].items() if v}
        if bonus: resultado["entrenamiento"][clave] = bonus
        else: resultado["entrenamiento"].pop(clave, None)
        if any(registro["equipo_indices"]): equipo.append(personaje["nombre"])
    resultado["partida_sha256"] = huella
    return resultado, {"encontrados": len(vistos), "con_equipo": equipo}


def _guardar_calibracion(datos):
    temporal = FICHERO_CALIB.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(FICHERO_CALIB)

def _sumar_entrenamiento(valor, bonus):
    total = valor + bonus
    return 1 if total < 0 else total  # 0x490484: el cero se conserva

def stats_nivel(p, nivel, rates=None):
    ajustes = (rates or {}).get("bases", {}).get(p.get("clave"), {})
    entrenamiento = (rates or {}).get("entrenamiento", {}).get(p.get("clave"), {})
    elemento = p.get("elemento_id")
    if elemento is None:
        elemento = next((k for k, v in ELEMENTOS.items() if v == p["elemento"]), 0)
    return {s: _sumar_entrenamiento(stat_juego(ajustes.get(s, p["base"][s]), p["curva"][s], nivel, i,
                          elemento, p["perfil"]), entrenamiento.get(s, 0)) for i, s in enumerate(STATS)}

def _fmt(v):
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else str(v)
    except (TypeError, ValueError):
        return str(v)

def _lineas_xlsx(ruta):
    import zipfile, xml.etree.ElementTree as ET
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(ruta); nombres = z.namelist()
    compartidas = []
    if "xl/sharedStrings.xml" in nombres:
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(ns + "si"):
            compartidas.append("".join(t.text or "" for t in si.iter(ns + "t")))
    hoja = "xl/worksheets/sheet1.xml" if "xl/worksheets/sheet1.xml" in nombres else sorted(n for n in nombres if n.startswith("xl/worksheets/sheet"))[0]
    lineas = []
    for fila in ET.fromstring(z.read(hoja)).iter(ns + "row"):
        celdas = []
        for c in fila.findall(ns + "c"):
            t = c.get("t"); v = c.find(ns + "v")
            if t == "s" and v is not None: val = compartidas[int(v.text)]
            elif t == "inlineStr": val = "".join(x.text or "" for x in c.iter(ns + "t"))
            elif v is not None and v.text is not None: val = _fmt(v.text) if t != "str" else v.text
            else: val = ""
            if str(val).strip(): celdas.append(str(val).strip())
        lineas.append(" ".join(celdas))
    return lineas

def _lineas_ods(ruta):
    import zipfile, xml.etree.ElementTree as ET
    T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
    X = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
    O = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
    raiz = ET.fromstring(zipfile.ZipFile(ruta).read("content.xml"))
    tabla = next(raiz.iter(T + "table"))
    lineas = []
    for fila in tabla.iter(T + "table-row"):
        celdas = []
        for c in fila:
            if c.tag not in (T + "table-cell", T + "covered-table-cell"): continue
            v = c.get(O + "value")
            val = _fmt(v) if v is not None else " ".join("".join(p.itertext()) for p in c.iter(X + "p"))
            if str(val).strip():
                rep = min(int(c.get(T + "number-columns-repeated", "1")), 50)   # celdas iguales contiguas
                celdas.extend([str(val).strip()] * rep)
        lineas.append(" ".join(celdas))
    return lineas

def _lineas_ejemplos(ruta):
    ext = str(ruta).lower().rsplit(".", 1)[-1]
    if ext == "xlsx": return _lineas_xlsx(ruta)
    if ext == "ods": return _lineas_ods(ruta)
    return Path(ruta).read_text(encoding="utf-8-sig").splitlines()

def leer_ejemplos(ruta):
    """Filas: Nombre  Posicion  Nivel  PE PT Elemento Tiro Regate Tecnica Defensa Rapidez Aguante Control Suerte"""
    filas = []
    for linea in _lineas_ejemplos(ruta):
        t = linea.replace("\u00a0", " ").replace(";", " ").replace(",", " ").replace('"', " ").split()
        if len(t) < 14 or not t[-12].isdigit(): continue          # cabecera o linea invalida
        try:
            nivel = int(t[-12]); pe, pt = int(t[-11]), int(t[-10]); resto = [int(x) for x in t[-8:]]
        except ValueError:
            continue
        filas.append((" ".join(t[:-13]), nivel, [pe, pt] + resto))
    return filas

def contrastar_referencias(bd, filas, rates=None):
    """Deduce solo bases compatibles con TODAS las observaciones de una stat.

    Nunca altera curvas, perfiles ni formula. Un salto de pasiva se resta solo
    si el cambio de residuo es exactamente 10/20 y hay 1 o 2 niveles de diferencia,
    o si skill_table acredita la habilidad aprendida en ese intervalo.
    Las contradicciones se conservan en el informe; no se promedian ni interpolan.
    """
    from collections import defaultdict
    grupos = defaultdict(list)
    for nombre, nivel, valores in filas:
        if not NIVEL_MIN <= nivel <= NIVEL_MAX:
            raise ValueError("Nivel fuera de rango en la tabla: %s" % nivel)
        grupos[norm(nombre)].append((nivel, valores))
    resultado = dict(rates or {})
    resultado.update({"modelo": MODELO, "bases": dict((rates or {}).get("bases", {}))})
    informe = {"filas": len(filas), "valores": 0, "coincidencias": 0,
               "series_compatibles": 0, "pasivas": [], "incompatibles": [],
               "sin_encontrar": [], "ambiguos": [], "comprobaciones": []}
    for nombre, obs in grupos.items():
        encontrados = [p for p in bd if norm(p["nombre"]) == nombre]
        if not encontrados:
            informe["sin_encontrar"].append(nombre); continue
        if len(encontrados) != 1:
            informe["ambiguos"].append(nombre); continue
        p = encontrados[0]
        if "clave" not in p:
            raise ValueError("Vuelve a cargar los datos: falta identidad del personaje")
        ajustes = dict(resultado["bases"].get(p["clave"], {}))
        for i, stat in enumerate(STATS):
            base_original = p["base"][stat]
            def calcular(base, nivel):
                return _sumar_entrenamiento(stat_juego(base, p["curva"][stat], nivel, i, p["elemento_id"], p["perfil"]), (rates or {}).get("entrenamiento", {}).get(p["clave"], {}).get(stat, 0))
            serie = sorted((nivel, valores[i]) for nivel, valores in obs)
            normalizados = []; bonus = 0; anterior = None
            for nivel, valor in serie:
                residuo = valor - calcular(base_original, nivel)
                if anterior is not None:
                    nivel_ant, residuo_ant = anterior
                    salto = residuo - residuo_ant
                    acreditado = sum(h["bonus"] for h in p.get("pasivas", [])
                                      if h["stat"] == stat and nivel_ant < h["nivel"] <= nivel)
                    if salto in (10, 20) and (1 <= nivel - nivel_ant <= 2 or acreditado == salto):
                        bonus += salto
                        informe["pasivas"].append({"nombre": p["nombre"], "stat": stat,
                            "desde": nivel_ant, "hasta": nivel, "bonus": salto,
                            "fuente": "skill_table" if acreditado == salto else "salto_corto"})
                normalizados.append((nivel, valor - bonus))
                anterior = (nivel, residuo)
            candidatos = [base for base in range(256)
                          if all(calcular(base, n) == v for n, v in normalizados)]
            informe["valores"] += len(normalizados)
            if len(candidatos) == 1:
                base = candidatos[0]
                if base != base_original: ajustes[stat] = base
                else: ajustes.pop(stat, None)
                informe["series_compatibles"] += 1
            else:
                # No reutilizar una correccion previa que contradice la nueva tabla.
                ajustes.pop(stat, None)
                errores = [{"nivel": n, "referencia": v, "calculado": calcular(base_original, n)}
                           for n, v in normalizados if calcular(base_original, n) != v]
                informe["incompatibles"].append({"nombre": p["nombre"], "stat": stat,
                    "candidatos": candidatos, "errores": errores})
            base_final = ajustes.get(stat, base_original)
            for nivel, referencia in normalizados:
                calculado = calcular(base_final, nivel)
                informe["coincidencias"] += calculado == referencia
                informe["comprobaciones"].append({"nombre": p["nombre"], "stat": stat,
                    "nivel": nivel, "referencia_sin_pasiva": referencia,
                    "calculado": calculado, "coincide": calculado == referencia})
        if ajustes: resultado["bases"][p["clave"]] = ajustes
        else: resultado["bases"].pop(p["clave"], None)
    return resultado, informe

def calibrar(bd, ruta, rates, log=print):
    filas = leer_ejemplos(ruta)
    if not filas:
        raise ValueError("No se pudo leer ninguna fila valida.")
    nuevos, informe = contrastar_referencias(bd, filas, rates)
    for destino, datos in [(FICHERO_CALIB, nuevos),
                            (FICHERO_CALIB.with_name("contraste_referencias.json"), informe)]:
        temporal = destino.with_suffix(".tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(destino)
    log("Filas: %d | valores compatibles: %d/%d | stats incompatibles: %d" %
        (len(filas), informe["coincidencias"], informe["valores"], len(informe["incompatibles"])))
    if informe["sin_encontrar"]: log("No encontrados: " + ", ".join(informe["sin_encontrar"]))
    if informe["ambiguos"]: log("Nombres ambiguos (sin modificar): " + ", ".join(informe["ambiguos"]))
    for pasiva in informe["pasivas"]:
        log("Pasiva restada: %(nombre)s %(stat)s +%(bonus)d entre niveles %(desde)d y %(hasta)d" % pasiva)
    for error in informe["incompatibles"]:
        log("Sin ajuste compatible: %(nombre)s / %(stat)s; consulta contraste_referencias.json" % error)
    log("Bases coherentes guardadas en %s; formula del juego conservada." % FICHERO_CALIB)
    return nuevos

# ----------------------------------------------------------------------------------
# 6) Interfaz de texto
# ----------------------------------------------------------------------------------
def buscar(bd, texto):
    t = norm(texto)
    exactos = [p for p in bd if t in (norm(p["nombre"]), norm(p["corto"]))]
    return exactos or [p for p in bd if t in norm(p["nombre"])]

def elegir(bd, texto):
    res = buscar(bd, texto)
    if not res:
        print("  No encontrado: %s" % texto); return None
    if len(res) == 1: return res[0]
    for i, p in enumerate(res[:15], 1): print("  %d) %s" % (i, p["nombre"]))
    try: return res[int(input("  Elige numero: ")) - 1]
    except (ValueError, IndexError): return None

def pedir_nivel():
    while True:
        try:
            n = int(input("Nivel (%d-%d): " % (NIVEL_MIN, NIVEL_MAX)))
            if NIVEL_MIN <= n <= NIVEL_MAX: return n
        except ValueError: pass

def opcion_consulta(bd, rates):
    p = elegir(bd, input("Personaje: "))
    if not p: return
    n = pedir_nivel(); s = stats_nivel(p, n, rates)
    print("\n%s - nivel %d - Elemento: %s" % (p["nombre"], n, p["elemento"]))
    for k in STATS: print("  %-9s %d" % (k, s[k]))

def opcion_ranking(bd, rates):
    pos = list(POSICIONES)
    for i, k in enumerate(pos, 1): print("  %d) %s" % (i, k))
    try: pos = pos[int(input("Posicion: ")) - 1]
    except (ValueError, IndexError): return
    n = pedir_nivel()
    nombres = input("Nombres separados por coma (vacio = toda la base de datos): ").strip()
    grupo = []
    if nombres:
        for t in nombres.split(","):
            p = elegir(bd, t)
            if p and p not in grupo: grupo.append(p)
    else:
        grupo = bd
    pesos = POSICIONES[pos]; filas = []
    for p in grupo:
        s = stats_nivel(p, n, rates)
        filas.append((sum(s[k] * w for k, w in pesos.items()) / sum(pesos.values()), p, s))
    filas.sort(key=lambda x: -x[0])
    top = len(filas) if nombres else int(input("Cuantos mostrar (ej. 20): ") or 20)
    print("\nRanking %s - nivel %d (pesos: %s)" % (pos, n, pesos))
    for i, (sc, p, s) in enumerate(filas[:top], 1):
        print("%3d. %-28s %6.1f   %s" % (i, p["nombre"], sc, " ".join("%s:%d" % (k[:4], s[k]) for k in pesos)))

def calcular_ranking(grupo, pos, nivel, rates):
    """Devuelve [(puntuacion, personaje, stats)] ordenado de mejor a peor."""
    pesos = POSICIONES[pos]; filas = []
    for p in grupo:
        s = stats_nivel(p, nivel, rates)
        filas.append((sum(s[k] * w for k, w in pesos.items()) / sum(pesos.values()), p, s))
    filas.sort(key=lambda x: -x[0])
    return filas

def main_cli():
    ruta = sys.argv[2] if len(sys.argv) > 2 else input("Ruta del archivo (.7z o ie_a.fa): ")
    bd = cargar_bd(ruta); rates = cargar_rates()
    print("%d personajes cargados." % len(bd))
    while True:
        print("\n1) Stats de un personaje a un nivel   2) Ranking por posicion\n3) Cambiar archivo                    4) Calibrar con tabla de ejemplos\n5) Salir                            6) Importar entrenamiento de partida")
        o = input("> ").strip()
        if o == "1": opcion_consulta(bd, rates)
        elif o == "2": opcion_ranking(bd, rates)
        elif o == "3":
            bd = cargar_bd(input("Ruta: ")); print("%d personajes cargados." % len(bd))
        elif o == "4":
            rates = calibrar(bd, input("Ruta de la tabla (.xlsx, .ods, .csv, .tsv o .txt): ").strip().strip('"'), rates)
        elif o == "6":
            try:
                nuevos, informe = importar_entrenamiento(bd, input("Ruta de game.ie4: ").strip().strip('"'), rates)
                _guardar_calibracion(nuevos)
                rates = nuevos
                print("Entrenamiento importado: %d jugadores. Equipo y pasivas no incluidos." % informe["encontrados"])
            except (OSError, ValueError) as e:
                print("No se pudo importar: %s" % e)
        elif o == "5": break

# ----------------------------------------------------------------------------------
# 7) Interfaz grafica (tkinter, incluido con Python en Windows y macOS)
# ----------------------------------------------------------------------------------
class App:
    def __init__(self, tk, ttk, filedialog, messagebox, threading, ruta_inicial=""):
        self.tk, self.ttk, self.fd, self.mb, self.threading = tk, ttk, filedialog, messagebox, threading
        self.root = tk.Tk()
        self.root.title("Stats de personajes por nivel")
        self.root.geometry("980x640"); self.root.minsize(820, 520)
        try: ttk.Style().theme_use("clam")
        except Exception: pass
        self.bd = []; self.etiquetas = {}; self.rates = cargar_rates()
        self.resultado_carga = None

        # --- barra superior: archivo ---
        top = ttk.Frame(self.root, padding=8); top.pack(fill="x")
        ttk.Label(top, text="Archivo:").pack(side="left")
        self.var_ruta = tk.StringVar(value=ruta_inicial)
        ttk.Entry(top, textvariable=self.var_ruta).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(top, text="Examinar...", command=self.examinar).pack(side="left")
        self.btn_cargar = ttk.Button(top, text="Cargar", command=self.cargar)
        self.btn_cargar.pack(side="left", padx=(6, 0))
        ttk.Button(top, text="Importar entrenamiento...", command=self.importar_partida_gui).pack(side="left", padx=6)
        self.var_estado = tk.StringVar(value="Elige el archivo (.7z o ie_a.fa) y pulsa Cargar.")
        ttk.Label(self.root, textvariable=self.var_estado, padding=(10, 0, 10, 6), foreground="#444").pack(fill="x")

        # --- pestanas ---
        self.nb = ttk.Notebook(self.root); self.nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._tab_consulta(); self._tab_ranking(); self._tab_calibracion()
        if ruta_inicial:
            self.root.after(200, self.cargar)

    # ----- carga de archivo (en hilo para no congelar la ventana) -----
    def examinar(self):
        r = self.fd.askopenfilename(title="Archivo de datos",
            filetypes=[("7z o ARC0", "*.7z *.fa"), ("Todos", "*.*")])
        if r: self.var_ruta.set(r)

    def cargar(self):
        ruta = self.var_ruta.get().strip()
        if not ruta:
            self.mb.showwarning("Falta el archivo", "Indica la ruta del archivo."); return
        self.btn_cargar.config(state="disabled")
        self.var_estado.set("Cargando... (si es un .7z la primera vez tarda ~1 minuto)")
        self.resultado_carga = None
        def trabajo():
            try: self.resultado_carga = ("ok", cargar_bd(ruta))
            except Exception as e: self.resultado_carga = ("error", e)
        self.threading.Thread(target=trabajo, daemon=True).start()
        self.root.after(300, self._esperar_carga)

    def _esperar_carga(self):
        if self.resultado_carga is None:
            self.root.after(300, self._esperar_carga); return
        self.btn_cargar.config(state="normal")
        tipo, val = self.resultado_carga
        if tipo == "error":
            self.var_estado.set("Error al cargar.")
            self.mb.showerror("No se pudo cargar", str(val)); return
        self.bd = val
        self.etiquetas = {}
        for p in self.bd:
            et = p["nombre"]; k = 2
            while et in self.etiquetas: et = "%s #%d" % (p["nombre"], k); k += 1
            self.etiquetas[et] = p
        self.todas = sorted(self.etiquetas, key=norm)
        self.cb_personaje["values"] = self.todas[:300]
        self.var_estado.set("%d personajes cargados." % len(self.bd))

    def importar_partida_gui(self):
        if not self._requiere_datos(): return
        ruta = self.fd.askopenfilename(title="Partida exportada con Checkpoint/JKSM",
            filetypes=[("Guardado GO", "*.ie4"), ("Todos", "*.*")])
        if not ruta: return
        try:
            nuevos, informe = importar_entrenamiento(self.bd, ruta, self.rates)
            _guardar_calibracion(nuevos)
            self.rates = nuevos
        except (OSError, ValueError) as e:
            self.mb.showerror("No se pudo importar", str(e)); return
        self.var_estado.set("Entrenamiento importado: %d jugadores. Equipo y pasivas no incluidos." % informe["encontrados"])
        if informe["con_equipo"]:
            self.mb.showinfo("Equipo no incluido", "La partida contiene jugadores con equipo; sus bonus no se importan.")

    def _requiere_datos(self):
        if not self.bd:
            self.mb.showinfo("Sin datos", "Primero carga un archivo."); return False
        return True

    # ----- pestana 1: consulta -----
    def _tab_consulta(self):
        tk, ttk = self.tk, self.ttk
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text="Consulta")
        fila = ttk.Frame(f); fila.pack(fill="x")
        ttk.Label(fila, text="Personaje:").pack(side="left")
        self.var_pers = tk.StringVar()
        self.cb_personaje = ttk.Combobox(fila, textvariable=self.var_pers, width=34)
        self.cb_personaje.pack(side="left", padx=6)
        self.cb_personaje.bind("<KeyRelease>", self._filtrar_personajes)
        self.cb_personaje.bind("<Return>", lambda e: self.consultar())
        ttk.Label(fila, text="Nivel:").pack(side="left", padx=(12, 0))
        self.var_niv_c = tk.IntVar(value=1)
        ttk.Spinbox(fila, from_=NIVEL_MIN, to=NIVEL_MAX, textvariable=self.var_niv_c, width=5).pack(side="left", padx=6)
        ttk.Button(fila, text="Calcular", command=self.consultar).pack(side="left", padx=6)
        self.var_cab = tk.StringVar()
        ttk.Label(f, textvariable=self.var_cab, font=("TkDefaultFont", 13, "bold"), padding=(0, 12, 0, 6)).pack(anchor="w")
        cols = ("stat", "base", "nivel", "dif")
        self.tv_c = ttk.Treeview(f, columns=cols, show="headings", height=12)
        for c, t, w in (("stat", "Stat", 160), ("base", "Base (nivel 1)", 120), ("nivel", "En el nivel elegido", 160), ("dif", "Diferencia", 100)):
            self.tv_c.heading(c, text=t); self.tv_c.column(c, width=w, anchor="center")
        self.tv_c.pack(fill="x")

    def _filtrar_personajes(self, ev=None):
        if ev is not None and ev.keysym in ("Return", "Up", "Down", "Tab"): return
        t = norm(self.var_pers.get())
        if not self.etiquetas: return
        vals = [e for e in self.todas if t in norm(e)] if t else self.todas
        self.cb_personaje["values"] = vals[:300]

    def consultar(self):
        if not self._requiere_datos(): return
        texto = self.var_pers.get().strip()
        p = self.etiquetas.get(texto)
        if p is None:
            res = buscar(self.bd, texto)
            if len(res) == 1: p = res[0]
            elif not res:
                self.mb.showinfo("No encontrado", "No hay ningun personaje llamado '%s'." % texto); return
            else:
                self.mb.showinfo("Varios resultados", "Hay %d coincidencias; elige una de la lista desplegable." % len(res))
                self._filtrar_personajes(); return
        try: n = int(self.var_niv_c.get())
        except Exception: n = -1
        if not NIVEL_MIN <= n <= NIVEL_MAX:
            self.mb.showwarning("Nivel no valido", "El nivel debe estar entre %d y %d." % (NIVEL_MIN, NIVEL_MAX)); return
        s = stats_nivel(p, n, self.rates)
        self.var_cab.set("%s  -  nivel %d  -  Elemento: %s" % (p["nombre"], n, p["elemento"]))
        self.tv_c.delete(*self.tv_c.get_children())
        iniciales = stats_nivel(p, NIVEL_MIN, self.rates)
        for k in STATS:
            self.tv_c.insert("", "end", values=(k, iniciales[k], s[k], "%+d" % (s[k] - iniciales[k])))

    # ----- pestana 2: ranking -----
    def _tab_ranking(self):
        tk, ttk = self.tk, self.ttk
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text="Ranking por posicion")
        izq = ttk.Frame(f); izq.pack(side="left", fill="y", padx=(0, 12))
        ttk.Label(izq, text="Posicion:").pack(anchor="w")
        self.var_pos = tk.StringVar(value=list(POSICIONES)[0])
        cb = ttk.Combobox(izq, textvariable=self.var_pos, values=list(POSICIONES), state="readonly", width=16)
        cb.pack(anchor="w"); cb.bind("<<ComboboxSelected>>", lambda e: self._mostrar_pesos())
        self.var_pesos = tk.StringVar(); ttk.Label(izq, textvariable=self.var_pesos, wraplength=170, foreground="#444").pack(anchor="w", pady=(2, 8))
        ttk.Label(izq, text="Nivel:").pack(anchor="w")
        self.var_niv_r = tk.IntVar(value=1)
        ttk.Spinbox(izq, from_=NIVEL_MIN, to=NIVEL_MAX, textvariable=self.var_niv_r, width=6).pack(anchor="w", pady=(0, 8))
        self.var_modo = tk.StringVar(value="todos")
        ttk.Radiobutton(izq, text="Toda la base de datos", variable=self.var_modo, value="todos", command=self._modo).pack(anchor="w")
        ttk.Radiobutton(izq, text="Solo estos nombres:", variable=self.var_modo, value="lista", command=self._modo).pack(anchor="w")
        self.txt_nombres = tk.Text(izq, width=24, height=9, state="disabled"); self.txt_nombres.pack(anchor="w", pady=4)
        ttk.Label(izq, text="(uno por linea o separados por coma)", foreground="#666").pack(anchor="w")
        fila = ttk.Frame(izq); fila.pack(anchor="w", pady=(8, 0))
        ttk.Label(fila, text="Mostrar los mejores:").pack(side="left")
        self.var_top = tk.IntVar(value=20)
        self.sp_top = ttk.Spinbox(fila, from_=1, to=2000, textvariable=self.var_top, width=6); self.sp_top.pack(side="left", padx=4)
        ttk.Button(izq, text="Calcular ranking", command=self.ranking).pack(anchor="w", pady=10)
        der = ttk.Frame(f); der.pack(side="left", fill="both", expand=True)
        cols = ("n", "nombre", "punt", "elem") + tuple(STATS)
        self.tv_r = ttk.Treeview(der, columns=cols, show="headings")
        anchos = {"n": 40, "nombre": 170, "punt": 70, "elem": 70}
        etiq = {"n": "#", "nombre": "Nombre", "punt": "Punt.", "elem": "Elem."}
        for c in cols:
            self.tv_r.heading(c, text=etiq.get(c, c)); self.tv_r.column(c, width=anchos.get(c, 62), anchor="center" if c != "nombre" else "w", stretch=(c == "nombre"))
        sb = ttk.Scrollbar(der, orient="vertical", command=self.tv_r.yview); self.tv_r.configure(yscrollcommand=sb.set)
        self.tv_r.pack(side="left", fill="both", expand=True); sb.pack(side="left", fill="y")
        self._mostrar_pesos(); self._modo()

    def _mostrar_pesos(self):
        w = POSICIONES[self.var_pos.get()]
        self.var_pesos.set("Pesos: " + ", ".join("%s x%d" % (k, v) for k, v in w.items()))

    def _modo(self):
        lista = self.var_modo.get() == "lista"
        self.txt_nombres.config(state="normal" if lista else "disabled")
        self.sp_top.config(state="disabled" if lista else "normal")

    def ranking(self):
        if not self._requiere_datos(): return
        try: n = int(self.var_niv_r.get())
        except Exception: n = -1
        if not NIVEL_MIN <= n <= NIVEL_MAX:
            self.mb.showwarning("Nivel no valido", "El nivel debe estar entre %d y %d." % (NIVEL_MIN, NIVEL_MAX)); return
        pos = self.var_pos.get(); faltan = []
        if self.var_modo.get() == "lista":
            texto = self.txt_nombres.get("1.0", "end").replace(",", "\n")
            nombres = [t.strip() for t in texto.split("\n") if t.strip()]
            if not nombres:
                self.mb.showinfo("Sin nombres", "Escribe al menos un nombre."); return
            grupo = []
            for t in nombres:
                res = buscar(self.bd, t)
                if not res: faltan.append(t)
                for p in res:
                    if p not in grupo: grupo.append(p)
            top = len(grupo)
        else:
            grupo = self.bd
            try: top = int(self.var_top.get())
            except Exception: top = 20
        filas = calcular_ranking(grupo, pos, n, self.rates)
        self.tv_r.delete(*self.tv_r.get_children())
        for i, (sc, p, s) in enumerate(filas[:top], 1):
            self.tv_r.insert("", "end", values=(i, p["nombre"], "%.1f" % sc, p["elemento"]) + tuple(s[k] for k in STATS))
        self.var_estado.set("Ranking %s, nivel %d: %d personajes mostrados." % (pos, n, min(top, len(filas))))
        if faltan:
            self.mb.showinfo("Nombres no encontrados", "No se encontraron:\n" + "\n".join(faltan))

    # ----- pestana 3: calibracion -----
    def _tab_calibracion(self):
        tk, ttk = self.tk, self.ttk
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text="Calibracion")
        ttk.Label(f, wraplength=860, justify="left", text=(
            "Se usa la formula del juego (curva, elemento y perfil). Elige una tabla (.xlsx de Excel, .ods de LibreOffice, .csv o .txt) con personajes y sus stats reales a distintos "
            "niveles (columnas: Nombre, Posicion, Nivel, PE, PT, Elemento, Tiro, Regate, Tecnica, Defensa, Rapidez, Aguante, Control, "
            "Suerte). Solo se corrigen bases coherentes con todos sus niveles; se informan las contradicciones. "
            "Se restan pasivas de +10/+20 entre niveles separados por 1 o 2. Se guarda en calibracion.json.")).pack(anchor="w")
        fila = ttk.Frame(f); fila.pack(anchor="w", pady=8)
        ttk.Button(fila, text="Elegir tabla y calibrar...", command=self.calibrar_gui).pack(side="left")
        ttk.Button(fila, text="Restablecer valores por defecto", command=self.restablecer).pack(side="left", padx=8)
        self.txt_log = tk.Text(f, height=16, state="disabled"); self.txt_log.pack(fill="both", expand=True)

    def _log(self, texto):
        self.txt_log.config(state="normal"); self.txt_log.insert("end", str(texto) + "\n")
        self.txt_log.see("end"); self.txt_log.config(state="disabled")

    def calibrar_gui(self):
        if not self._requiere_datos(): return
        r = self.fd.askopenfilename(title="Tabla de ejemplos", filetypes=[("Tablas (Excel, LibreOffice, CSV)", "*.xlsx *.ods *.csv *.tsv *.txt"), ("Todos", "*.*")])
        if not r: return
        try: self.rates = calibrar(self.bd, r, self.rates, log=self._log)
        except Exception as e: self.mb.showerror("Error al calibrar", str(e))

    def restablecer(self):
        try:
            if FICHERO_CALIB.exists(): FICHERO_CALIB.unlink()
        except OSError: pass
        self.rates = {"modelo": MODELO, "bases": {}}; self._log("Valores por defecto restablecidos.")

    def run(self):
        self.root.mainloop()

def main_gui(ruta_inicial=""):
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        import threading
    except ImportError:
        print("No se pudo cargar tkinter (interfaz grafica). Se usa el modo texto.")
        return main_cli()
    App(tk, ttk, filedialog, messagebox, threading, ruta_inicial).run()

def main():
    args = sys.argv[1:]
    if args and args[0] == "--cli":
        return main_cli()
    main_gui(args[0] if args else "")

if __name__ == "__main__":
    main()
