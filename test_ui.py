from app.ui import banner, table, separator, green, yellow, red, cyan, bold, dim
banner("ACE Framework")
table(["ID", "Name", "Steps"], [["hello-ace", "Hello ACE", "3"]], [20, 20, 10])
separator()
print(green("✓ Success"))
print(red("✗ Failed"))
