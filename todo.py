# Simple CLI todo list

todos = []

while True:
    print('\nTodo menu:')
    print('1. Add task')
    print('2. List tasks')
    print('3. Remove task')
    print('4. Quit')

    choice = input('Choose an option: ').strip()

    if choice == '1':
        task = input('Task: ').strip()
        if task:
            todos.append(task)
            print('Added.')
        else:
            print('Empty task ignored.')
    elif choice == '2':
        if not todos:
            print('No tasks yet.')
        else:
            for i, task in enumerate(todos, start=1):
                print(f'{i}. {task}')
    elif choice == '3':
        if not todos:
            print('No tasks to remove.')
            continue
        idx = input('Number to remove: ').strip()
        if idx.isdigit():
            n = int(idx)
            if 1 <= n <= len(todos):
                removed = todos.pop(n - 1)
                print(f'Removed: {removed}')
            else:
                print('Invalid number.')
        else:
            print('Please enter a number.')
    elif choice == '4':
        print('Bye!')
        break
    else:
        print('Unknown option.')
