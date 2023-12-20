# GN format hook for pre-commit

[GN](https://gn.googlesource.com/gn/+/main/docs/reference.md#cmd_format) package for [pre-commit](http://pre-commit.com).

## Using gn-format with pre-commit

```yaml
-   repo: https://github.com/KindDragon/pre-commit-gn-format.git
    rev: main
    hooks:
    -   id: gn-format
```
