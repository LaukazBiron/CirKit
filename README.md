```markdown
# CirKit - Simulador de Circuitos Eléctricos

## Descripción del Proyecto
**CirKit** es una aplicación desarrollada en Python que permite realizar cálculos fundamentales en circuitos eléctricos. Este proyecto fue desarrollado como parte del curso de Administración de Proyectos y sirve como herramienta educativa para el análisis de circuitos básicos.

## Características Principales
- **Ley de Ohm** - Cálculo de voltaje, corriente y resistencia
- **Resistencias en serie y paralelo** - Combinación de múltiples resistencias
- **Potencia eléctrica** - Cálculo de potencia en circuitos
- **Interfaz modular** - Separación entre lógica de negocio e interfaz de usuario

## Instalación y Configuración

### Requisitos del Sistema
- Python 3.13.7 o superior
- Git para control de versiones

### Instalación
1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/LaukazBiron/CirKit.git
   cd CirKit
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación:**
   ```bash
   # Versión de consola
   python ejecutable.py
   
   # Versión con interfaz gráfica (Tkinter)
   python interfaz_tkinter.py
   
   # Versión con interfaz gráfica (Kivy)
   python interfaz_kivy.py
   ```

## Instrucciones de Uso

### Modo Consola
Ejecute el archivo principal y seleccione una opción del menú:
```bash
python ejecutable.py
```

Opciones disponibles:
1. Ley de Ohm
2. Resistencias en serie
3. Resistencias en paralelo
4. Potencia eléctrica

### Ejemplo de Cálculo
```python
# Añadir
```

## Estructura del Proyecto
```
calculadora-circuitos/
├── README.md                 # Documentación del proyecto
├── LICENSE                   # Licencia MIT
├── calculadora.py            # Versión principal de consola
├── interfaz_tkinter.py       # Interfaz gráfica con Tkinter
├── interfaz_kivy.py          # Interfaz gráfica con Kivy
├── logica_circuitos.py       # Lógica de cálculos y funciones
├── requirements.txt          # Dependencias del proyecto
└── .gitignore               # Archivos ignorados por Git
```

## Gestión de Ramas
El proyecto utiliza un sistema de ramas para el desarrollo organizado:

- **`main`** - Rama principal con versiones estables
- **`interfaz`** - Desarrollo de la interfaz gráfica
- **`backend`** - Desarrollo de la lógica de negocio

### Comandos para Cambiar entre Ramas
```bash
# Cambiar a rama de interfaz
git checkout interfaz

# Cambiar a rama de backend
git checkout backend

# Volver a la rama principal
git checkout main
```

## Equipo de Desarrollo

### Integrantes del Proyecto
- Gael Askary Razo Montañez - Lider de Proyecto / Arquitecto de Software
- Oscar Uriel Garcia Vera - Diseñador / Desarrollador UI
- Limhi Gerson Lopez Momox - Controlador de Versiones / Supervisor de Proyecto
- Juan Enrique Gutierrez Hernández - Control de Calidad / Controlador de Documentos
- Arturo Huerta Maldonado - Analista de Requerimientos / Desarrollador UX

### Responsabilidades
- **Desarrollo Backend**: Lógica de cálculos y funciones
- **Desarrollo Frontend**: Interfaz de usuario (Tkinter/Kivy)
- **Documentación**: Manuales y guías de usuario
- **Pruebas**: Verificación de funcionalidades

## Metodología de Desarrollo
- **Control de Versiones**: Git con GitHub
- **Gestión de Ramas**: Feature branch workflow
- **Documentación**: Markdown
- **Pruebas**: Pruebas unitarias para funciones críticas

## Objetivo general: Simulación de circuitos por diseño "CirKit"

### Fase 1: Diseño de la interfaz grafica
- [x] Creación del boceto 
- [x] Desarrollo de los componentes (botones)
- [x] Creación de 4 plantillas
- [x] Prueba de la interfaz
- [x] Evaluación del prototipo

### Fase 2: Implementación de 3 componentes básicos
- [x] Diseño e investigación de la lógica
- [x] Desarrollo temprano backend
- [x] Creación de clases
- [x] Programación del metodo
- [x] Conección de logica con interfaz

### Fase 3: Supervisar pruebas y correccione
- [x] Pruebas de funcionalidad
- [x] Corrección de errores
- [x] Documentación técnica
- [x] Manual de usuario
- [x] Presentación

## Contribución al Proyecto
Para contribuir al proyecto, siga estos pasos:

1. **Crear una rama para la nueva funcionalidad:**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

2. **Realizar commits descriptivos:**
   ```bash
   git commit -m "Descripción clara de los cambios"
   ```

3. **Sincronizar con el repositorio remoto:**
   ```bash
   git push origin feature/nueva-funcionalidad
   ```

4. **Crear un Pull Request** para revisión

## Reporte de Problemas
Si encuentra algún error o tiene sugerencias de mejora:

1. Verifique la pestaña "Issues" en GitHub
2. Cree un nuevo issue con una descripción detallada
3. Incluya pasos para reproducir el problema
4. Especifique su entorno de trabajo

## Tecnologías Utilizadas
- **Lenguaje de Programación**: Python 3.8+
- **Interfaz Gráfica**: Tkinter y Kivy
- **Control de Versiones**: Git
- **Plataforma de Colaboración**: GitHub
- **Documentación**: Markdown

## Licencia
Este proyecto está bajo la Licencia MIT. Consulte el archivo [LICENSE](LICENSE) para más detalles.

---

## Estado Actual del Proyecto
**En Desarrollo** - Versión funcional básica completada


---

**Proyecto Académico** - Curso de Administración de Proyectos  
**Institución**: Benemérita Universidad Autónoma de Puebla
**Fecha de Entrega**: 17/21 de Noviembre de 2025
```
