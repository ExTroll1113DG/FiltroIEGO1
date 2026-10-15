Programa de estadísticas de Inazuma Eleven GO Light.

Con Python 3.8+ y sin paquetes externos:

    python programa.py ie_a.fa
    python programa.py --cli ie_a.fa

Conserva calibracion.json junto al programa. Contiene el entrenamiento de Aguante +5 de Dan, acreditado en la partida, sin alterar su base. El cálculo usa las curvas reales, elemento y perfil del juego.

Para actualizar el entrenamiento usa «Importar entrenamiento...» en la ventana o la opción 6 en texto, seleccionando game.ie4 exportado con Checkpoint/JKSM. Se comprueba su CRC y se lee sin modificarlo. No se incluyen equipo ni pasivas en las stats calculadas; la app avisa si la partida contiene equipo. Al importar se retiran calibraciones de base de los jugadores importados para evitar contar dos veces un entrenamiento; después puedes contrastar de nuevo el Excel.

La pestaña Calibración conserva la fórmula y solo acepta bases coherentes con todos los niveles observados. Al contrastar referencias descuenta pasivas acreditadas o saltos de +10/+20 entre niveles separados por uno o dos.

Verificación (en el proyecto completo):

    python -m unittest discover -s tests
    python research/validate_real_data.py data/ie_a.fa

Estado: 876/880 valores confirmados coinciden. Quedan cuatro stats de Sapp a nivel 1 confirmadas por foto y aún sin explicación; el segundo comando falla mientras persistan. Los 19 tests no ocultan esa limitación. Ver PROGRESS.md, TODO.md y RESEARCH.md.

Libro1_confirmado.xlsx contiene únicamente las correcciones autorizadas de Faye y Esteban. El original se conserva intacto. El fixture tests/fixtures/players_go.ie4 está minimizado para pruebas y NO es una partida para restaurar.
