## error ##

```python
fpdf.error(msg: str)
```

### Description ###

This method is automatically called in case of fatal error; it simply outputs the message and halts the execution. An inherited class may override it to customize the error handling but should always halt the script, or the resulting document would probably be invalid.

### Parameters ###

msg:
> The error message.


