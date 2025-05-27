# db-tools
A tool for managing simulation output files

---

## 1. Output directory

Output files must be stored in a directory named `output/`

- Can be changed with `--prefix`

---

## 2. Output file naming and format

The simulation script must produce a file named `<fileroot>_info.npz`

- `<fileroot>` can be anything, but acts as a unique identifier for the run  
- This file must contain a dictionary under the key `'inputs'` with the input parameters from the run  
- Other associated data (e.g., large sampling arrays) should be stored in separate files using the same root name (e.g., `<fileroot>_samples.npz`)

---

## 3. Input parameter specification

The tool comes with a set of default accepted input parameters defined in `dbtools.inputs.json`.

- Accepted input parameters can be dynamically appended using a file with the same name in the current working directory (the directory from which you run the dbtools command)
- The input parameters are fully replaced if a file named `dbtools.inputs.replace.json` is present in the current working directory

---

## 4. Command structure
- Basic command structure (order of single-dash and double-dash flags is interchangeable)
    - `dbtools <command> [--command-options] [-simulation-parameters]`
- Input parameters are given by **single-dash** flags (e.g., `-omega`, `-E0`, `-dt`)  
- **Double-dash** flags (e.g., `--prefix`, `--print-style`) are specific to each `<command>`

---

## 🔍 Usage Examples

### Print `fileroot` and all input parameters for matching runs  
(update --fast is run automatically unless `--no-update`):

```bash
dbtools search -E0=0.01 -omega=0.057
```
### Search and print only parameters that are not the same in all entries.
```bash
dbtools search -E0=0.01 -omega=0.057 --print-style=diff
```

### Scan output directory and update the database with entries from the output files
```bash
dbtools update
```
### Update and remove database entries for missing output files
```bash
dbtools update --prune
```
### Update, but skip files already present in the database
(does not catch changes in existing _info.npz files)
```bash
dbtools update --fast
```

### Print differing inputs between two entries
```bash
dbtools diff <fileroot1> <fileroot2>
```

### Delete database entry and related output files
```bash
dbtools delete <fileroot>
```