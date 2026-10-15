# Estado — 2026-10-16
Objetivo: corregir programa.py (stats por nivel, rankings y filtros), sin ajustes arbitrarios. No es ie_randomizer.

## Implementado y validado
- data/ie_a.fa extraído;1001personajes. Modelo ARM0x33E404: curvas1–9, elemento, perfil, float32 y truncado;40000casos emulados sin discrepancias.
- GUI/CLI, consultas, rankings y filtros probados realmente.19tests pasan. El contraste completo sigue876/880; validador devuelve1, no declarar corrección completa.
- Excel original intacto. research/Libro1_confirmado.xlsx solo corrige Faye Control16 al7 y Esteban Regate43 al12, autorizado por usuario; trazabilidad en reference_corrections.json.
- Pasivas Tommie Control+10 al13 y Cyber Tiro+10 al15 acreditadas y descontadas del contraste.

## Nuevo hallazgo de Checkpoint y cambio en app
Checkpoint recibido y descifrado con CRC válido: game.ie4 =48960bytes, cabecera0x2CF1; head.ie4 =208bytes, CRC válido. Originales intactos:
/workspace/attachments/14503e25-c5ed-48ca-8280-fcd35013fb8c/game.ie4
/workspace/attachments/5b590ca5-e66f-4b07-9dcd-d9a4f65ce015/head.ie4
SHA256 y detalles en research/checkpoint_analysis.json. Tabla desde0x3488,204bytes por jugador,22IDs reconocidos. Estado resumido en save_players_inspection.json.
Dan tiene entrenamiento Aguante+5. Se retiró base48: programa mantiene base43 y suma entrenamiento después del crecimiento. calibracion.json ahora bases={} y entrenamiento={claveDan:{Aguante:5}}. NO volver a describirlo como base real48.
App permite importar entrenamiento de game.ie4 en GUI y opción6 CLI, solo lectura y CRC obligatorio. No importa equipo ni pasivas como entrenamiento. Fixture minimizado en tests/fixtures/players_go.ie4; no restaurarlo en consola. GUI de importación y CLI probadas, ajustes idempotentes.

## Sapp y límite de evidencia
Foto desde equipo/jugadores, recién fichado al1, equipo vacío: PE76/PT68/Técnica31/Control17; demás stats coinciden. Foto y observación se mantienen válidas. Evidencia en sapp_level1_photo_evidence.json.
Rutina natural y de inicialización2FBE6C dan75/67/32/19. Bloque345FC0 de AddMemberMain copia bases y coincide10/10 con foto, pero NO está acreditado como origen de esa pantalla del equipo. Emulaciones, fixtures y excerpt en research/verify_*arm.py y *_arm_validation.json.
Colby/Faye/Ambrose también recién fichados sin experiencia y coinciden con fórmula. No aplicar regla universal nivel1=base ni excepción para Sapp.
Partida actual confirma Sapp nivel6, paramID258738238/baseID44562404 (mismos que archivo), entrenamiento0 y equipo0. No conserva sus stats naturales del nivel1. No explica todavía la foto. PE/PT actuales de22jugadores no superan máximos calculados, incluidas pasivas conocidas.
El usuario ya subió Sapp y no puede repetir guardar/recargar al1. NO volver a pedir esa prueba, la misma foto, ni exportar Checkpoint otra vez. La partida ya es legible; el .sav bruto anterior quedó irrelevante para inspección actual.

## Siguiente acción exacta
Continuar desde la condición de estado/presentación que selecciona bases frente a crecimiento; no volver a investigar cifrado ni parser ya resueltos. Si llega evidencia nueva de un fichaje reproducible, enlazarlo con callbacks AddMember0x257DA8/0x259580 y ficha de equipo, sin adivinar contexto. Archivo de diagnóstico sapp_level1_diagnosis.json sigue describiendo las cuatro diferencias, no una solución.
No hay justificación para alterar fórmula, anclar una tabla por nombre/nivel o eliminar referencias. Lo no resuelto exige reproducir el estado inicial: el snapshot actual no permite recuperarlo. Con cualquier corrección sustentada ejecutar tests y research/validate_real_data.py, actualizar paquete programa_corregido.zip y estos tres archivos. Mantener fallo explícito mientras siga876/880.

## Entrega guardada
Paquete programa_corregido.zip regenerado a petición del usuario y verificado byte a byte contra programa.py, calibracion.json y README.md. Consulta ejecutada Esteban nivel12: 89/95/78/43/72/24/41/34/24/49. Sin cambios de modelo; siguen las cuatro diferencias de Sapp documentadas.

## Publicación autorizada
El usuario autorizó subir la app a ExTroll1113DG/FiltroIEGO1. Entrega: programa.py, calibracion.json, README.md y programa_corregido.zip, con los documentos de continuidad. Se excluyen partidas, ejecutable y archivos del juego. La investigación y sus pruebas completas permanecen en el entorno de trabajo.
