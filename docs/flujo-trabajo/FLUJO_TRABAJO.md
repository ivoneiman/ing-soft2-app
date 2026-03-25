# Flujo de trabajo con ramas (Git)

## 1️⃣ Partir siempre desde `develop` actualizado
```bash
git checkout develop
git pull origin develop
```
> **¿Por qué?**
> - `develop` contiene la última versión estable del código.
> - Evita que tu rama arranque con cambios obsoletos y reduce conflictos al hacer merge.

## 2️⃣ Crear la rama para lo que vas a trabajar
**Formato del nombre:**
| Tipo | Prefijo | Ejemplo |
|------|---------|---------|
| Nueva funcionalidad visible | `feature/` | `feature/registro-login-email` |
| Tarea de configuración / scripts | `chore/` | `chore/setup-flask-migrate` |
| Refactorización sin cambiar la API | `refactor/` | `refactor/models-dominio` |
| Documentación / diagramas | `docs/` | `docs/wireframes` |
| Scripts Bash / prototipos | `bashfeature/` | `bashfeature/modelo-clase-actividad` |

```bash
git checkout -b <prefijo>/<nombre-descriptivo> develop
# Ejemplo:
git checkout -b feature/modelo-inscripcion develop
```
> **¿Por qué?**
> - El prefijo indica el tipo de trabajo y facilita la búsqueda de ramas.
> - El nombre descriptivo permite identificar rápidamente el alcance de la tarea.

## 3️⃣ Desarrollar, commitear seguido y con mensajes descriptivos
```bash
# 1) Añadir los cambios al staging
git add .

# 2) Commits atómicos y claros
git commit -m "feat: agregar modelo Inscripcion con relaciones"
git commit -m "feat: validar cupo máximo al inscribir"
git commit -m "test: agregar test de inscripción superando cupo"
```
> **Buenas prácticas**
> - Cada commit debe contener **una sola idea** (una funcionalidad, una validación, un test, etc.).
> - Usa el formato `tipo: mensaje` (`feat`, `fix`, `test`, `chore`, `refactor`, `docs`).
> - Si la rama se aleja mucho de `develop`, haz `git fetch && git rebase origin/develop` antes de seguir comiteando.

## 4️⃣ Cuando terminás, merge a `develop`
```bash
# Volver a develop
git checkout develop

# Incorporar los cambios (preferible vía PR, pero también se puede hacer merge local)
git merge feature/modelo-inscripcion
```
> **¿Por qué?**
> - `develop` sigue siendo la rama “línea base” donde se integran todas las funcionalidades.
> - El merge después de una revisión (PR) garantiza que el código ha sido auditado y probado.

## 5️⃣ Borrar la rama que ya no se necesita
```bash
git branch -d feature/modelo-inscripcion          # elimina localmente
git push origin --delete feature/modelo-inscripcion   # elimina en remoto
```
> **Ventaja**: Mantiene el listado de ramas limpio y evita confusiones en futuros desarrollos.

---
### 📌 Resumen rápido (todo en una sola lista)
```bash
# 1. actualizar develop
git checkout develop && git pull origin develop

# 2. crear rama
git checkout -b <prefijo>/<nombre> develop

# 3. trabajar + commits
git add .
git commit -m "feat: …"
# (repetir según sea necesario)

# 4. merge a develop
git checkout develop
git merge <prefijo>/<nombre>

# 5. borrar rama
git branch -d <prefijo>/<nombre>
git push origin --delete <prefijo>/<nombre>
```

---
### ✅ Principios del flujo
1. **Siempre partir de `develop` actualizado**.
2. **Nombrado consistente** (`feature/…`, `chore/…`, `refactor/…`, `docs/…`, `bashfeature/…`).
3. **Commits atómicos y descriptivos** con el prefijo `feat:`, `fix:`, `test:`, etc.
4. **Revisión vía Pull‑Request** antes del merge a `develop`.
5. **Limpiar ramas** una vez integradas.

Con este documento todos tendrán una guía clara y uniforme para trabajar con Git durante el proyecto.