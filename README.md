## Setup
Require
- python >=3.9
- poetry

```shell
$ poetry update
```

## Test
- Run all testes
```shell
$ make pytest
```


- Run only specific test (replace args N with the desired wanted test (`01__test.py`, `02__test.py` etc))
```shell
$ N=1 make only_test
```


- Run the main algo test
```shell
$ make algo_test
```
