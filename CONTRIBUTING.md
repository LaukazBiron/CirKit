# Guía de Desarrollo Interno - CirKit

Esta guía está dirigida exclusivamente a los miembros del equipo de desarrollo del proyecto CirKit.

## Integrantes del Equipo

- **Gael Askary Razo Montañez** - Líder de Proyecto / Arquitecto de Software
- **Oscar Uriel Garcia Vera** - Diseñador / Desarrollador UI
- **Limhi Gerson Lopez Momox** - Controlador de Versiones / Supervisor de Proyecto
- **Juan Enrique Gutierrez Hernández** - Control de Calidad / Controlador de Documentos
- **Arturo Huerta Maldonado** - Analista de Requerimientos / Desarrollador UX

## Flujo de Trabajo del Equipo

### Rama Principal (`main`)
- Solo acepta código mediante **Pull Requests**
- Siempre debe estar en estado estable
- Requiere **revisión de al menos 1 compañero** antes del merge

### Ramas de Desarrollo
- `interfaz` - Desarrollo de interfaz gráfica con Kivy
- `backend` - Lógica de simulación de circuitos
- `feature/nombre-feature` - Para nuevas funcionalidades específicas

### Proceso de Desarrollo

1. **Sincronizar antes de empezar:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Crear rama de feature:**
   ```bash
   git checkout -b feature/nombre-feature
   ```

3. **Desarrollar y hacer commits:**
   ```bash
   git add .
   git commit -m "tipo: descripción clara"
   ```

4. **Sincronizar con main periódicamente:**
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/nombre-feature
   git merge main
   ```

5. **Crear Pull Request en GitHub**
   - Asignar revisores del equipo
   - Esperar aprobación antes de merge

## Estándares Técnicos

### Estructura de Proyecto
```
src/
├── app/          # simulate.py, export_pdf.py
├── domain/       # netlist.py, components/
└── ui/kivy/      # InterfazMain.py, InterfazMain.kv
```

### Convención de Commits
- `feat:` Nueva funcionalidad
- `fix:` Corrección de bugs
- `docs:` Documentación
- `refactor:` Reestructuración de código
- `test:` Pruebas

### Pruebas Locales
Antes de hacer PR, verificar:
- [ ] El código ejecuta sin errores
- [ ] La interfaz carga correctamente
- [ ] Los cálculos de circuitos son precisos
- [ ] No se rompió funcionalidad existente

## Responsabilidades por Rol

### Líder de Proyecto
- Aprobar Pull Requests finales
- Coordinar integración de módulos
- Supervisar arquitectura general

### Controlador de Versiones
- Revisar estructura de commits
- Gestionar conflictos de merge
- Mantener limpieza de ramas

### Control de Calidad
- Probar funcionalidades integradas
- Verificar cálculos matemáticos
- Validar interfaz de usuario

## Comunicación del Equipo

- Usar **Issues de GitHub** para reportar bugs
- **Pull Requests** para revisión de código
- Comunicar cambios que afecten múltiples módulos

## Entrega Final

**Fecha límite: 21 de Noviembre de 2024**

Criterios de aceptación:
- [ ] Código completamente integrado
- [ ] Documentación actualizada
- [ ] Ejecutable funcionando
- [ ] Pruebas realizadas
- [ ] Presentación preparada
