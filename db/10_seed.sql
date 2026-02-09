-- Sample tasks so that the UI and PvP can work out of the box.
INSERT INTO tasks (title, statement, subject, topic, difficulty, answer_type, correct_answer, hints_json)
VALUES
  (
    '2 + 2',
    'Сколько будет 2 + 2? Введите одно целое число.',
    'Математика',
    'Арифметика',
    1,
    'int',
    '4',
    JSON_ARRAY('Сложите два числа.', 'Это базовая проверка автопроверки.')
  ),
  (
    'Столица Франции',
    'Введите столицу Франции (одно слово).',
    'Общее',
    'Факты',
    1,
    'text',
    'Париж',
    JSON_ARRAY('Подсказка: Эйфелева башня.')
  ),
  (
    'YES/NO',
    'Введите YES.',
    'Общее',
    'Тест',
    1,
    'text',
    'YES',
    JSON_ARRAY('Проверьте регистр: сравнение без учета регистра.')
  );
