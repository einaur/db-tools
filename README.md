# db-tools
A tool for managing simulation output files

---

## 1. Output directory

Output files must be stored in a directory named `output/`

- Can be changed with `--prefix`

---

## 2. Output file naming and format

The simulation script must produce a file named either `<fileroot>_info.json` or `<fileroot>_info.npz`

- `<fileroot>` can be anything (e.g., a UUID), but acts as a unique identifier for the run
- This file must contain a dictionary under the key `'inputs'` with the input parameters from the run
- Example content for a `.json` file (the `.npz` file should have the same structure):

  ```json
  {
    "inputs": {
        "E0": 0.01,
        "omega": 0.057,
        "dt": 0.05
    }
  }
  ```
- Other associated data (e.g., large sampling arrays) should be stored in separate files using the same root name (e.g., `<fileroot>_samples.npz`)

---

## 3. Input parameter specification

The tool comes with a set of default accepted input parameters defined in `dbtools.inputs.json`

- Accepted input parameters can be dynamically appended using a file with the same name in the current working directory (the directory from which you run the dbtools command)
- The input parameters are fully replaced if a file named `dbtools.inputs.replace.json` is present in the current working directory
- If no such files are found locally, the tool will look for `inputs.json` and `inputs.replace.json` in the configuration directory `~/.config/dbtools/` using the same logic (replace takes precedence over append).

---

## 4. Command structure
- Basic command structure (order of single-dash and double-dash flags is interchangeable)
    - `dbtools <command> [--command-options] [-simulation-parameters]`
- Input parameters are given by **single-dash** flags (e.g., `-omega`, `-E0`, `-dt`)  
- **Double-dash** flags (e.g., `--prefix`, `--print-style`) are specific to each `<command>`
- The commands have short forms (e.g., `s` for `search`, `pd` or `diff` for `print_diff`) — run `dbtools --help` to see the full list

---

## 🔍 Usage Examples

### Print `fileroot` and all input parameters for matching runs  
(update --fast is run automatically unless `--no-update`):

```text
dbtools search -E0=0.01 -omega=0.057
```
### Search and print only parameters that are not the same in all entries.
```text
dbtools search -E0=0.01 -omega=0.057 --print-style=diff
```

### Scan output directory and update the database with entries from the output files
```text
dbtools update
```
### Update and remove database entries for missing output files
```text
dbtools update --prune
```
### Update, but skip files already present in the database
(does not catch changes in existing _info.npz files)
```text
dbtools update --fast
```

### Print differing inputs between two entries
```text
dbtools diff <fileroot1> <fileroot2>
```

### Delete database entry and related output files
```text
dbtools delete <fileroot>
```
