# Archimedius

A desktop app that organizes personal media files — audio, video, images, and ebooks — by reading each file's metadata and relocating it into a folder structure the user defines.

## Language

**Archimedius**:
The product. Use this name in domain language, issues, and user-facing descriptions — not the repo name (`media_organizer`) or legacy code identifiers.
_Avoid_: Media Organizer, MediaOrganizer, media_organizer

**Organize**:
The primary operation: scan files in a source location, read metadata, compute a destination path from a template, then copy or move each file into the destination tree.
_Avoid_: Sort, file (verb), curate, catalog

**Source**:
The folder the user points Archimedius at to find files to organize. Files are read from here; in move mode they may be removed from here after organizing.
_Avoid_: Input, inbox, input folder

**Destination**:
The root folder where organized files are written. Each file lands somewhere under this tree based on its template and metadata.
_Avoid_: Output, target, library root

**Template**:
A relative path pattern under the destination root, using `{placeholder}` tokens filled from a file's metadata (e.g. `{creation_year}/{genre}/{filename}`). Each media type has its own template.
_Avoid_: Path pattern, organization rule, folder scheme

**Operation mode**:
How an organize run transfers files: copy (source files remain) or move (source files are removed after a successful transfer). Both modes are organizing — not separate features.
_Avoid_: Transfer type, action, duplicate vs relocate

**Media type**:
One of four supported groupings — audio, video, image, ebook — each with its own template, extension list, and metadata fields. A file's media type is inferred from its extension.
_Avoid_: File category, format family, content type

**Unrecognized file**:
A file whose extension is not in any media type's configured extension list. These files are skipped during organize — not a fifth media type.
_Avoid_: Unknown file, unsupported file, unclassified

**Missing metadata**:
A metadata field with no value extracted from the file. When a template placeholder references missing metadata, the generated path uses a fallback segment (currently the folder name `Unknown`).
_Avoid_: Unknown metadata, empty tag, null field

**Exclude unknown**:
A per-media-type setting that omits path segments produced from missing metadata, rather than creating `Unknown` folders in the destination tree.
_Avoid_: Skip unknown, hide unknown folders, strip unknown segments

**Metadata**:
Facts about a file used to build destination paths — both embedded tags (artist, genre, title from the file) and file properties (filename, size, creation date from the filesystem).
_Avoid_: Tags (alone), properties (alone), attributes

**Placeholder**:
A `{token}` in a template replaced with a metadata value when computing a file's destination path (e.g. `{genre}`, `{creation_year}`, `{filename}`).
_Avoid_: Metadata key, field, variable, token

**Preview**:
A simulated organize that shows each file's source path and computed destination path without copying or moving files. Triggered by the Analyze button in the UI.
_Avoid_: Analyze, dry run, scan

**Organize run**:
An actual organize operation that transfers files (in copy or move mode). Use this term when distinguishing from preview.
_Avoid_: Execute, process, batch, job

**Supported extensions**:
The per-media-type list of file extensions that determines which files are included in preview and organize runs. Users can customize these in preferences.
_Avoid_: File types, extension list, format list

**Settings**:
All persisted user configuration — source, destination, templates, supported extensions, exclude unknown, operation mode, and UI behavior — stored in the settings file.
_Avoid_: Config, configuration, options

**Preferences**:
The dialog where the user edits a subset of settings — mainly UI behavior (auto-preview, logging level, show full paths) and supported extensions. Not a separate persistence layer.
_Avoid_: Options dialog, config panel, setup

**Path collision**:
When two files would resolve to the same destination path during an organize run. Resolved via a collision policy — not silently overwritten or skipped by default.
_Avoid_: Duplicate path, naming conflict, overwrite

**Collision policy**:
The user's chosen response when a path collision occurs: rename, overwrite, or skip. A default policy lives in settings; the user can be prompted per collision, with an option to apply the choice to all remaining collisions in the run.
_Avoid_: Duplicate handling, conflict resolution, naming strategy

**Source scan**:
Discovery of files under the source folder, including all nested subfolders. Preview and organize runs scan recursively by default.
_Avoid_: Recursive scan, deep scan, folder walk

**Selected extensions**:
The per-run subset of extensions included in a preview or organize run, chosen via checkboxes on the main window. Filters which files are processed without changing supported extensions in settings.
_Avoid_: Active extensions, extension filter, enabled formats

**Stop**:
A user-initiated halt of an in-progress organize run. Files already transferred remain in the destination; the run ends without undoing completed transfers.
_Avoid_: Cancel, abort, rollback

**Destination path**:
The path where a file will land after organizing — computed from the destination root, the media type's template, and the file's metadata. Shown relative to the destination root unless full paths are enabled in settings.
_Avoid_: Organized path, resolved path, target path

## Example dialogue

> **Dev:** User picked `/Downloads/mess` as source and `/Media` as destination, audio template `{creation_year}/{genre}/{filename}`, copy mode. What happens to an `.mp3` tagged genre=Rock, year=2024?
>
> **Expert:** Archimedius runs a **source scan** — recursive under `/Downloads/mess`. The extension is in **supported extensions** for the **audio** **media type**, and the user has it in **selected extensions** for this run. **Metadata** fills the **placeholders** → **destination path** `2024/Rock/track.mp3` under `/Media`. **Preview** shows the pair without transferring. An **organize run** in copy **operation mode** copies the file there.
>
> **Dev:** Same file but no genre tag, exclude unknown off?
>
> **Expert:** **Missing metadata** for `{genre}` → segment `Unknown`. Path becomes `2024/Unknown/track.mp3`. With **exclude unknown** on, it collapses to `2024/track.mp3`.
>
> **Dev:** Another file would hit the same **destination path**?
>
> **Expert:** That's a **path collision**. **Collision policy** applies — default from **settings**, with a per-collision prompt and "apply to all" option. Not a silent overwrite.

## Flagged ambiguities

- **Path collision (implementation):** Help text describes automatic rename-on-collision; current organize code performs a direct copy/move with no collision handling. Intended behavior is user prompt (see **Path collision**). Code does not match yet.
- **Destination vs output:** Domain term is **destination**; code still uses `output_dir` in places.
