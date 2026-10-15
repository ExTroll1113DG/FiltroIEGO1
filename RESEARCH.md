# Evidencia inicial
- App original: RATES_DEFECTO={1:.604,2:.604,3:.990,4:.990,5:0,6:0,7:2.646,8:1.764,9:1.472}; g=(nivel-1)*rate; PE/PT floor; resto round Python.
- Excel Hoja1: filas 2–89; duplicado exacto Colby nivel 4 (filas 31/35); niveles 1–19. No se ha ajustado ningún dato todavía.
- Posibles pasivas: Tommie Control 64→74 nivel 11→13; Cyber Tiro 35→50 nivel 10→15 (este último NO satisface criterio explícito de diferencia <=2).
- Posible error de registro: Esteban Regate 43→42 nivel 11→12; conservar y diagnosticar.
- GitHub búsqueda HTML accesible: https://github.com/search?q=inazuma+eleven+go&type=repositories . API api.github.com bloqueada por proxy (403 CONNECT).
- Ejecutable contiene ruta data/res/character/chara_param.cfg.bin en offset 0x1872f0.

# Algoritmo localizado (avance 2)
- Fuente pública: https://github.com/Tiniifan/Lynx/blob/8d71bc7821bbec901743cc769c20d80fb08dad59/Lynx/InazumaEleven/Games/GO/GOStatCalculator.cs
- Esquema chara_param: mismo commit, Games/GO/GOSupport.cs. Columna 21 (índice cero) StatVariance = perfil. Elemento columna 12. Curvas columnas 23–32 correctas.
- Verificación independiente del ejecutable adjunto: función ARM 0x0033E404, switch 0x0033E4A4; tablas perfil (10x10 float32) en 0x00586C18 y elemento (4x10) en 0x00586DA8. Base carga byte [r0+0x16], curva [r0+0x20], perfil byte [r0+0x30], elemento [r0+0x14].
- Curvas 1/2 lineales distintas con multiplicadores elemento/perfil; 3/4 crecimiento temprano no lineal; 5/6 tardío no constante; 7/8/9 polinomios cuadráticos PE/PT independientes de elemento/perfil. 0 y desconocidos usan rama1.
- Nivel usado directamente (no nivel-1); todas las stats se truncan hacia cero tras cálculo float32, no round Python.
- Diferencia detectada en fuente Lynx: constante lineal curva8 C#=1.8554000854492188, ejecutable adjunto=1.8553999662399292 (bits 0x3fed7dbf). Prevalece el binario.
- Desensamblado completo guardado research/code.arm.txt; todavía no hay datos de chara_param del usuario para validar su archivo.
- Google búsqueda bloqueada 403 CONNECT; no se ha presentado como fuente consultada.

# Verificación del port
research/verify_arm.py usa Unicorn 2.1.4, ejecuta instrucciones reales desde 0x33E4A4 hasta 0x33E958, emula únicamente auxiliar entero cuadrado 0x157264. 40 000 comparaciones (10 perfiles × 4 elementos × 10 stats × 10 curvas × 10 niveles; bases aleatorias con semilla112), 0 discrepancias. Fixtures 1 800 en arm_validation.json para tests sin dependencias.
Correcciones implementadas: todas las curvas, dos tablas, float32 paso a paso, truncado, bases y pasivas compatibles por personaje/archivo (clave SHA256 del registro), rechazo de calibración lineal antigua, GUI nivel1 calculado.
Pruebas unitarias: 10 pasan. Se mantiene fórmula incluso ante referencias incompatibles.
Diagnóstico Excel aún SIN tablas originales: incompatibles en todos los perfiles probados: Tommie Control; Cyber Tiro; Esteban Regate; Faye Control; Sapp Técnica/Control. Son diagnósticos, no justificación para cambiar referencias ni fórmulas.
Descarga 10 partes completada (parte006 reintentada tras cierre de transporte); unión y extracción con py7zr en curso.

# Archivo real descargado y contraste
- Unión10partes =325911640 bytes; py7zr extracción correcta a data/ie_a.fa =855395144 bytes, ARC0.
- 1001 registros de personajes; 22/22 referencias encontradas sin duplicidades de nombre.
- Sin ajustes:869/880 celdas exactas. Dan Aguante +5 constante en3 niveles (base43→48 resuelve). Tommie Control +10 nivel11→13: pasiva según regla usuario.
- Anomalías restantes: Cyber Tiro nivel15 Excel50/juego40; Esteban Regate lv12 Excel42/juego43 (lv11=43); Faye Control lv7 Excel15/juego16 (lv6=15,lv8=17); Sapp lv1 Excel coincide literalmente con base de archivo, pero cálculo da PE75/PT67/Técnica32/Control19 en vez de76/68/31/17; lv2 y4 coinciden con rutina.
- Archivo reproducible inicial: research/initial_real_comparison.json. BD extraída research/characters.json; tablas en data/*.cfg.bin.

# Pasivas acreditadas y resultado final provisional
skill_table, índices49 y2944: Cyber aprende habilidad-2090564780 en15 (skill_config tipo15,efecto4=Tiro,bonus10); Tommie habilidad-217155621 en13 (efecto1=Control,bonus10). Se descuenta Cyber aun con intervalo observado5niveles porque hay evidencia directa, no inferencia por salto.
Dan Aguante tiene desfase constante+5 en niveles10,13,15. Según prioridad solicitada para Excel, calibracion.json guarda base48 frente43; no altera curvas ni fórmula.
Contraste posterior:874/880celdas coinciden,214/220series completas compatibles. Las6celdas pendientes constan en PROGRESS y final_real_comparison.json. El validador devuelve1 intencionalmente mientras existan.
No hay pasivas de stats en niveles bajos de Faye (skills6,22,31,48), Esteban (101,101,101,62) ni Sapp (23,46,53,60). No explican las6celdas.
GUI probada realmente con Xorg dummy:1001cargados, consulta Colby9 todoslos10valores,20puestos ranking99 y filtro2nombres. CLI mismos flujos correctos;12tests pasan. Ningún resultado se presenta como coincidencia completa con Excel.
Google y Reddit no accesibles por política CONNECT403; investigación pública sí realizada en GitHub (Lynx es fuente aplicable; UGR usa formato Galaxy distinto, no se ha transplantado).

# Confirmación del usuario (2026-10-16)
El usuario confirma Faye Control=16 a nivel7 y Esteban Regate=43 a nivel12. Conservado Libro1.xlsx original; creada copia Libro1_confirmado.xlsx con M66=16 y H88=43, trazabilidad en reference_corrections.json. Sapp nivel1 fue leído en el juego: se conservan sus10stats, NO se declara errata.
Rutina de presentación0x490484: suma stats naturales guardadas (offset0xD0), equipamiento (0xE4), entrenamiento signed16(0x20), pasivas signed8(0xEE). No recalcula crecimiento al mostrar. Por ello un estado almacenado puede diferir del recálculo; aún no se ha acreditado qué ocurrió en la partida de Sapp.
Inspección llamadas0x33E404: subida de nivel0x2FCCE0/0x2FCD44; establecimiento nivel0x24F300; inicialización0x2FBEF4/0x2FBF68; actualización0x2FD178. Las rutas observadas usan fórmula incluso nivel1; no se ha encontrado regla global "nivel1=base".

# Fichaje de Sapp: prueba ejecutada, no hipótesis (2026-10-16)
El usuario confirma fichaje al nivel 1 sin equipo y desconoce entrenamiento inicial.
research/verify_recruitment_arm.py ejecuta 0x2FBE6C hasta 0x2FBFBC, incluidas las dos llamadas reales a 0x33E404. Se sustituyen únicamente búsquedas de registros (0x2FBB40, 0x493AE4, 0x24F8CC, 0x24FA24) por estructuras que contienen los datos reales de cada personaje. Se inicializan los punteros a gestores; no se sustituyen instrucciones de cálculo.
Resultado Sapp: PE75 PT67 Tiro27 Regate42 Técnica32 Defensa54 Rapidez35 Aguante33 Control19 Suerte42. Colby, Faye y Ambrose también comprobados y coinciden con sus observaciones al nivel 1. Fixtures y salidas en recruitment_arm_validation.json.
Descartada como explicación acreditada la hipótesis de que esta ruta de fichaje copie las bases sin calcular crecimiento. Esto no invalida la observación del usuario: falta identificar su estado de juego real.
Referencias confirmadas ahora: 876/880 coincidencias; cuatro discrepancias de Sapp exclusivamente. 14 tests pasan, incluido control de las dos correcciones autorizadas y de los fixtures de fichaje; validador completo devuelve 1. Se ha solicitado captura/partida específica, sin solicitar datos ya contestados.

# Foto de Sapp y segunda ruta de presentación (2026-10-16)
Foto confirma nivel1, PE76/76 PT68/68, equipo vacío, stats27/42/31/54/35/33/17/42. Transcripción visual en research/sapp_level1_photo_evidence.json. No había archivo local de imagen accesible; se conserva la transcripción y la fotografía sigue en la conversación.
Búsqueda sistemática de bloques que leen los diez bytes base y escriben stats16bit localizó rutina0x345FC0. Bloque0x346058..0x3460FC fija nivel1 y copia bases literales a la estructura de presentación; PE/PT también se copian a sus campos actuales. A diferencia de0x33E404, no calcula crecimiento.
Llamadas desde0x257DA8,0x259580 y0x37E0F0; el último contexto sobrescribe algunas stats con0x490484. Las dos primeras requieren seguir comprobando condición de entrada. Esto acredita una segunda representación de stats en el juego, NO demuestra todavía qué ruta produjo la foto.
research/verify_display_arm.py ejecuta instrucciones originales del bloque con datos reales de Sapp, Colby, Faye y Ambrose. Salida Sapp coincide10/10 con foto; fixtures en display_base_arm_validation.json. Preguntado al usuario desde qué menú abrió la pantalla y si las otras referencias de nivel1 tuvieron experiencia previa. No se añade regla universal ni excepción de Sapp.

# Respuestas posteriores y descarte de generalizaciones
El usuario confirma que Colby, Faye y Ambrose al nivel1 también estaban recién fichados y sin experiencia previa. Confirma que la foto de Sapp se abrió desde equipo/jugadores. Por tanto NO se aplica "recién fichado=base" universalmente y NO se reclasifica su referencia como álbum sin evidencia.
La rutina0x345FC0 es utilizada por AddMemberMain (controlador0x258064, script data/menu/script/add_member.xs en0x258370), con SetupPrm0x25811C y campo de ID0xB3C; callbacks0x257DA8 y0x259580. Otra llamada0x37E0F0 sobrescribe algunas stats desde el estado de jugador. Excerpt acotado conservado en display_routes_excerpt.arm.txt para no repetir búsquedas.
El hallazgo explica cómo el juego puede construir esa representación, pero todavía no acredita por qué la observación desde equipo tiene esa representación. No se ha modificado programa.py ni se ha ajustado por nombre/nivel a partir de esta hipótesis.
Diagnóstico conservado en sapp_level1_diagnosis.json. Prueba externa solicitada: guardar y recargar SIN subir nivel, para distinguir stats transitorias de inicialización frente a estado persistente. La carga del jugador observada en0x2FD178 vuelve a calcular naturales con0x33E404. Una partida exportada sigue siendo posible evidencia posterior si recargar no discrimina.
15 tests pasan, incluidos foto y segundo bloque emulado. El contraste general continúa876/880; no se ha vuelto a ejecutar sin cambios en app/referencias.

El usuario indica que subió personajes para recopilar niveles del Excel y ya no puede ejecutar la prueba de recarga a nivel1. No hay resultado de dicha prueba: NO registrar como cambio ni como persistencia confirmada. Próxima evidencia requerida: partida exportada actual para analizar correspondencia de variante/entrenamiento/metadatos, sin presumir que conserva estado histórico.

# Partida adjunta 00000001.sav (2026-10-16)
- Entrada: /workspace/attachments/51f61be6-9f09-45d9-89b3-fd56a3a830e1/00000001.sav, 524288 bytes, SHA2566159055b766f12b8b565591d6e7c3b564e539e3c2b2a7c9846b360db48ee3768. Hash comprobado antes y después, sin modificar.
- No contiene firmas DISA/DIFF/DIFI/IVFC/SAVE/XPCK ni nombres internos legibles. Regiones no nulas alineadas a sectores; compatible con copia bruta cifrada, no identificación criptográfica definitiva.
- Comprobada envoltura Level-5 XORShift según StudioElevenLib commit ef6cb6de49d940c394b01f4a35018d17baae883f, Level5/Compression/XORShift/XORShift.cs (origen yw_save.py/togenyan). Probados archivo completo y límites de regiones activas: ninguna cabecera IE admitida. Script y salidas en inspect_uploaded_save.py y uploaded_save_inspection.json.
- Segunda comprobación: https://github.com/wwylele/3ds-save-tool , disa-extract.py sin directorio de salida (solo inspección): Error: Not a DISA format. El programa avisa que no verifica CMAC sin claves; no se ha declarado integridad de la partida ni extracción válida. README oficial indica que contenedores de SD cifrados requieren claves y que los ya descifrados se pueden extraer. Se solicita exportación Checkpoint/JKSM en vez de claves.
- NO se han leído IDs, stats ni entrenamiento de la partida. No afirmar lo contrario. No cambiar modelo para forzar las4diferencias.

# Exportación Checkpoint leída (2026-10-16)
- head.ie4 (208bytes), SHA256 fcdfc90c302b6126454477a738586e04051977435bb2b85e99c325976be73258; game.ie4 (48960bytes), SHA256 bda56bc8b745bd11076164d2b9ff650f2648b5b6e8a166731424717ece5b7f3d. CRC32 del prefijo cifrado coincide con el almacenado en ambos. Descifrados mediante envoltura XORShift de Level-5, sin modificar entradas. Cabecera de game descifrado en offset4 =0x2CF1 (GO europeo).
- Tabla de jugadores desde0x3488, registros204bytes:22IDs reconocidos, alineados y vinculados con chara_param. Todos sin equipo actual. Detalles no personales en save_players_inspection.json; resumen de integridad en checkpoint_analysis.json.
- Sapp: registro0x4478, paramID258738238, baseID44562404 (coinciden con ie_a.fa), nivel6, entrenamiento ocho ceros, equipo cuatro ceros. PE actual83/PT75 compatibles con cálculo; sus stats naturales históricas de nivel1 no se almacenan aquí. Esto no invalida foto ni identifica qué ruta de presentación produjo sus valores anteriores.
- Dan: registro0x3884, nivel16, entrenamiento [0,0,0,0,0,5,0,0], equipo vacío. Los5puntos corresponden a Aguante y explican exactamente el desfase constante del Excel. Se retiró la corrección de base48: ahora se mantiene43 y se suma entrenamiento5 DESPUÉS del crecimiento, como0x490484. Ninguna base corregida permanece en calibracion.json.
- App incorpora lectura opcional de game.ie4 (CRC obligatorio, modo solo lectura) e importación de entrenamiento por ID y hash del registro de datos. GUI botón Importar entrenamiento y CLI opción6. Equipo/pasivas no se importan como entrenamiento; se avisa si hay equipo. Snapshot nuevo sustituye entrenamiento anterior del conjunto actual y rechaza copias ambiguas con distinto entrenamiento. Guardado de ajustes atómico.
-19tests pasan, incluidos CRC corrupto rechazado, datos Sapp actuales, entrenamiento Dan en niveles1–99, importación idempotente, refresco de snapshot y ambigüedad. Fixture minimizado elimina nombres personales/progreso/inventario; no es guardado restaurable.
-GUI real bajo Xorg: carga1001, importa22, Dan Aguante57 al15, ranking99 correcto. CLI importación/consulta/persistencia idempotente probadas. Comparación completa permanece876/880 y devuelve1; las4diferencias siguen exclusivamente en Sapp nivel1.
