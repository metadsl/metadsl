from code_data import CodeData

print(CodeData.from_code((lambda: None).__code__))
