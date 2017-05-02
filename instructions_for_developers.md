# Instructions for ProPhyle developers

## CLI

* Only short command-line parameters should be used (e.g., `-L`).
* Parameters with a capital letter are switchers without arguments (e.g., `-R`).
* When possible, required program arguments should be passed through positional arguments (e.g., `-k 31`).


## Source codes

* Each program or script should contain a name of the author and the license (ideally MIT).
* Python scripts should follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

## Testing

* A-tests (small) are run on Travis. B-tests (big) are run only locally (they are too long to be tested after each commit).
* Every program should (ideally) have a unit test.