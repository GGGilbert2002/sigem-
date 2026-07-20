# CONTRIBUTING.md — Guía de Contribución al Proyecto SIGEM

## 1. Estructura de Ramas (GitFlow Adaptado)

```
main          → Código de producción. PROTEGIDA. Solo acepta merges via Pull Request aprobado.
develop       → Rama de integración. Todo el trabajo nuevo se fusiona aquí primero.
feature/*     → Nuevas funcionalidades.
fix/*         → Corrección de errores.
docs/*        → Cambios exclusivos de documentación.
test/*        → Adición o corrección de pruebas.
```

### Ejemplos de nombres de ramas válidos
```
feature/modulo-estadisticas
feature/pantalla-registro-personal
fix/error-carga-mapas-territoriales
fix/sidebar-franja-blanca
docs/actualizar-readme-diagramas
test/pruebas-unitarias-validadores
```

### Reglas de nomenclatura
- Usar **kebab-case** (minúsculas con guiones).
- Ser descriptivo pero conciso (máximo 5 palabras después del prefijo).
- Nunca trabajar directamente sobre `main` ni `develop`.

---

## 2. Estándar de Commits (Conventional Commits)

Todos los commits deben seguir este formato estricto:

```
<tipo>(<alcance opcional>): <descripción en imperativo, minúsculas>

[cuerpo opcional: explica el QUÉ y el POR QUÉ, no el CÓMO]

[pie opcional: referencias a tareas, breaking changes]
```

### Tipos permitidos

| Tipo | Cuándo usarlo |
|------|---------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de un error |
| `docs` | Cambios solo de documentación |
| `style` | Formato, espacios, punto y coma (sin cambio de lógica) |
| `refactor` | Refactorización sin nueva funcionalidad ni fix |
| `test` | Añadir o corregir pruebas |
| `chore` | Tareas de mantenimiento (dependencias, CI, gitignore) |
| `perf` | Mejora de rendimiento |

### Ejemplos de commits válidos

```
feat(dashboard): agregar contadores KPI animados con ease-out
fix(mapas): corregir error NoneType en nombres de estados venezolanos
docs(readme): agregar diagramas de arquitectura en Mermaid
test(validadores): agregar pruebas unitarias para validacion de cedula
chore(ci): configurar pipeline de GitHub Actions con flake8
refactor(graficos): unificar estructura de datos en graficos_controller
fix(sidebar): eliminar franja blanca en encabezado y pie del menu lateral
feat(login): redisenar ventana con estetica militar institucional
```

### Referencia a tareas del plan de desarrollo

Cuando un commit corresponde a una tarea del plan, incluir la referencia al final:

```
feat(personal): implementar formulario completo de registro (Tarea #8)
test(autenticacion): prueba unitaria para hash de contrasena (Tarea #15)
```

---

## 3. Flujo de Trabajo para Nuevas Funcionalidades

```
1. Actualizar develop local:
   git checkout develop
   git pull origin develop

2. Crear rama de trabajo desde develop:
   git checkout -b feature/nombre-descriptivo

3. Desarrollar y commitear con Conventional Commits.

4. Subir la rama al repositorio remoto:
   git push origin feature/nombre-descriptivo

5. Abrir un Pull Request en GitHub:
   - Base: develop  ←  Compare: feature/nombre-descriptivo
   - Descripción: qué se hizo, por qué, cómo probarlo.
   - Asignar al menos un revisor.

6. Esperar la aprobación del revisor y que el pipeline CI pase (✅ verde).

7. Hacer merge del PR (Squash and Merge recomendado).

8. Eliminar la rama de trabajo después del merge.
```

---

## 4. Reglas de Pull Request

- El título del PR debe seguir el mismo formato de Conventional Commits.
- El PR debe incluir una descripción con: qué se cambió, por qué, y cómo verificarlo.
- **No se puede hacer merge sin**: (a) al menos 1 aprobación, (b) pipeline CI en verde.
- Nunca hacer `git push --force` sobre `main` ni `develop`.

---

## 5. Definition of Done (DoD)

Una tarea se considera terminada cuando:

- [ ] El código pasa el linter (`flake8`) sin errores.
- [ ] Las pruebas unitarias pasan en GitHub Actions (pipeline verde).
- [ ] Fue revisado y aprobado en un Pull Request.
- [ ] Las funciones y módulos tienen docstrings en español.
- [ ] Está referenciado correctamente en la bitácora de cambios (commits).
