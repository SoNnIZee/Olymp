# Simple calculator for two numbers

a = float(input('Enter first number: '))
b = float(input('Enter second number: '))

print('Sum:', a + b)
print('Difference:', a - b)
print('Product:', a * b)
print('Quotient:', a / b if b != 0 else 'undefined (division by zero)')
