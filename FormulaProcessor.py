import re
from collections import OrderedDict

class FormulaProcessor:
    """Класс для обработки математических формул и создания шаблонов"""
    
    # Словарь для транслитерации русских букв в латиницу
    RU_TO_EN = {
        'а': 'a', 'в': 'v', 'е': 'e', 'к': 'k', 'м': 'm', 'н': 'n', 
        'о': 'o', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'х': 'h'
    }
    
    # Буквы для замены переменных в шаблонах
    VAR_LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                   'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    
    @staticmethod
    def normalize_variable_name(var_name):
        """
        Нормализует имя переменной: транслитерирует русские буквы,
        оставляет латиницу, остальные символы сохраняет как есть.
        """
        result = ''
        for char in var_name:
            if char.lower() in FormulaProcessor.RU_TO_EN:
                result += FormulaProcessor.RU_TO_EN[char.lower()]
            elif char.isalpha() and char.isascii():
                result += char
            else:
                result += char
        return result
    
    @staticmethod
    def extract_variables(formula, exclude=None):
        """
        Извлекает все переменные из формулы.
        
        Args:
            formula: строка с формулой
            exclude: список переменных для исключения (или одна переменная)
        
        Returns:
            list: список уникальных переменных в порядке появления
        """
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude]
        
        # Находим все переменные (слова, начинающиеся с буквы)
        variables = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9а-яА-Я_]*\b', formula)
        
        # Исключаем ненужные переменные
        variables = [v for v in variables if v not in exclude]
        
        # Сохраняем порядок появления, убираем дубликаты
        seen = OrderedDict()
        for var in variables:
            if var not in seen:
                seen[var] = None
        
        return list(seen.keys())
    
    @staticmethod
    def _replace_abs(expression):
        """Заменяет модули |x| на abs(x) итеративно для обработки вложенных модулей"""
        result = expression
        # Ищем пары |...| без вложенных | внутри (самые внутренние)
        max_iterations = 10 
        for _ in range(max_iterations):
            new_result = re.sub(r'\|([^|]+)\|', r'abs(\1)', result)
            if new_result == result:
                break
            result = new_result
        return result

    @staticmethod
    def _replace_powers_temp(expression):
        """Заменяет степени на вызовы pow (без префикса Math.)"""
        # Сначала обрабатываем выражения в скобках: (a+b)^2
        expression = re.sub(r'\(([^)]+)\)\^(\d+\.?\d*)', 
                          lambda m: f"pow({m.group(1)}, {m.group(2)})", 
                          expression)
        # Затем простые базы: x^2, 2^3
        expression = re.sub(r'([a-zA-Z0-9]+)\^(\d+\.?\d*)', 
                          lambda m: f"pow({m.group(1)}, {m.group(2)})", 
                          expression)
        return expression

    @staticmethod
    def convert_math_functions(expression):
        if not expression:
            return expression
        
        result = expression.strip()
        
        # Модули: |x| → abs(x)
        result = FormulaProcessor._replace_abs(result)
        
        # Степени: x^2 → pow(x, 2)
        result = FormulaProcessor._replace_powers_temp(result)
        
        # Аркфункции
        result = re.sub(r'\basin\s*\(([^)]+)\)', r'asin(\1 * Math.PI/180)', result)
        result = re.sub(r'\bacos\s*\(([^)]+)\)', r'acos(\1 * Math.PI/180)', result)
        result = re.sub(r'\batan\s*\(([^)]+)\)', r'atan(\1 * Math.PI/180)', result)
        
        # Тригонометрические функции
        result = re.sub(r'\bsin\s*\(([^)]+)\)', r'sin(\1)', result)
        result = re.sub(r'\bcos\s*\(([^)]+)\)', r'cos(\1)', result)
        result = re.sub(r'\btan\s*\(([^)]+)\)', r'tan(\1)', result)
        
        #  Экспонента и натуральный логарифм
        result = re.sub(r'\bexp\s*\(([^)]+)\)', r'exp(\1)', result)
        result = re.sub(r'\bln\s*\(([^)]+)\)', r'log(\1)', result)
        
        # Логарифмы с основанием: log2(x) → log(x)/log(2)
        # Формат с подчеркиванием: log_2(x)
        result = re.sub(r'log_([a-zA-Z0-9]+)\s*\(([^)]+)\)', r'log(\2) / log(\1)', result)
        # Формат без подчеркивания (только цифры и 'e' во избежание конфликтов)
        result = re.sub(r'log([0-9eE]+)\s*\(([^)]+)\)', r'log(\2) / log(\1)', result)
        
        # Простой логарифм (натуральный)
        result = re.sub(r'\blog\s*\(([^)]+)\)', r'log(\1)', result)
        
        # Константа pi
        result = re.sub(r'\bpi\b', 'Math.PI', result)
        
        # Добавляем префикс Math. ко всем функциям 
        result = re.sub(r'\b(atan2|atan|asin|acos|exp|log|pow|tan|cos|sin|abs)\s*\(', 
                       r'Math.\1(', result)
        
        return result
    
    @staticmethod
    def create_formula_template(left_part, right_part):
        """
        Создает шаблон формулы с нормализацией переменных.
        """
        # Сохраняем оригинальную формулу без пробелов
        original_no_spaces = f"{left_part}={right_part}".replace(" ", "")
        
        template = "y="
        
        # Находим все переменные в правой части
        right_vars = FormulaProcessor.extract_variables(right_part)
        
        # Создаем словарь замен с сохранением порядка
        var_mapping = OrderedDict()
        var_counter = 0
        
        # Токенизация правой части
        tokens = re.findall(
            r'[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\^\d+|'
            r'[a-zA-Zα-ωΑ-ΩΔ][a-zA-zα-ωΑ-Ω0-9_]*|'
            r'\d+\^\d+|\S', 
            right_part
        )
        
        result_tokens = []
        for token in tokens:
            # Проверяем, является ли токен переменной со степенью
            if re.match(r'^[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\^\d+$', token):
                # Разделяем переменную и степень
                var_part, exp_part = token.split('^')
                
                if var_part != left_part and not var_part.isdigit():
                    # Нормализуем имя переменной перед созданием шаблона
                    normalized_var = FormulaProcessor.normalize_variable_name(var_part)
                    if normalized_var not in var_mapping:
                        var_mapping[normalized_var] = FormulaProcessor.VAR_LETTERS[var_counter]
                        var_counter += 1
                    
                    result_tokens.append(f"{var_mapping[normalized_var]}^{exp_part}")
                else:
                    result_tokens.append(token)
            
            # Проверяем, является ли токен простой переменной
            elif (re.match(r'^[a-zA-Zα-ωΑ-ΩΔ]', token) and 
                  token != left_part and
                  not token.isdigit() and '^' not in token): 
                
                # Нормализуем имя переменной перед созданием шаблона
                normalized_var = FormulaProcessor.normalize_variable_name(token)
                if normalized_var not in var_mapping:
                    var_mapping[normalized_var] = FormulaProcessor.VAR_LETTERS[var_counter]
                    var_counter += 1
                
                result_tokens.append(var_mapping[normalized_var])
            else:
                result_tokens.append(token)
        
        template_right = ''.join(result_tokens)
        
        # комплексное преобразование всех математических функций
        template_right = FormulaProcessor.convert_math_functions(template_right)
        
        template += template_right.replace(" ", "")
        
        # Создаем канонический шаблон (без русских и греческих букв)
        canonical_template = FormulaProcessor.create_canonical_template(template)
        
        return template, canonical_template
    
    @staticmethod
    def create_canonical_template(template):
        """Создает канонический шаблон без русских и греческих букв"""
        canonical = re.sub(r'[а-яА-Я]', '', template)  # Убираем русские буквы
        canonical = re.sub(r'[α-ωΑ-Ω]', '', canonical)  # Убираем греческие буквы
        return canonical
    
    @staticmethod
    def create_relation_from_template(canonical_template):
        """
        Создает relation из канонического шаблона.
        
        Returns:
            dict: словарь с параметрами relation
        """
        if not canonical_template.startswith("y="):
            return None
        
        formula_part = canonical_template[2:]
        variables_in_template = re.findall(r'\b[a-z]\b', formula_part)
        input_vars = sorted(set(variables_in_template))
        
        in_obj_parts = [f"{var}:double" for var in input_vars]
        in_obj = ";".join(in_obj_parts) if in_obj_parts else " "
        out_obj = "y:double"
        
        return {
            'shortName': canonical_template,
            'inObj': in_obj,
            'outObj': out_obj,
            'relationType': 'simple',
            'formula': canonical_template
        }
    
    @staticmethod
    def create_var_mapping(original_vars, template_vars):
        """
        Создает маппинг между шаблонными и оригинальными переменными.
        
        Args:
            original_vars: список оригинальных переменных
            template_vars: список переменных в шаблоне
        
        Returns:
            tuple: (var_mapping, rev_var_mapping)
        """
        var_mapping = {}
        rev_var_mapping = {}
        
        if len(original_vars) == len(template_vars):
            for i, t_var in enumerate(template_vars):
                if i < len(original_vars):
                    var_mapping[t_var] = original_vars[i]
                    rev_var_mapping[original_vars[i]] = t_var
        else:
            # Если количество не совпадает, пробуем сопоставить по позициям
            for i, t_var in enumerate(template_vars):
                if i < len(original_vars):
                    var_mapping[t_var] = original_vars[i]
                    rev_var_mapping[original_vars[i]] = t_var
                else:
                    # Если не хватает оригинальных переменных, используем шаблонную
                    var_mapping[t_var] = t_var
                    rev_var_mapping[t_var] = t_var
        
        return var_mapping, rev_var_mapping
    
    @staticmethod
    def is_formula(text):
        """Проверяет, является ли текст формулой"""
        return any(sym in text for sym in '=+-*/^()')


class FormulaRegistry:
    """Класс для управления реестром формул и отношений"""
    
    def __init__(self):
        self.formulas = []  # Все обработанные формулы
        self.canonical_templates = set()  # Уникальные канонические шаблоны
        self.template_to_relation = {}  # Маппинг шаблон -> relation
        self.canonical_to_relation = {}  # Маппинг канонический шаблон -> relation name
        self.original_to_canonical = {}  # Маппинг оригинальный шаблон -> канонический
        self.processed_formulas = set()  # Множество обработанных формул (для исключения дубликатов)
    
    def add_formula(self, formula_info):
        """Добавляет формулу в реестр"""
        self.formulas.append(formula_info)
        self.canonical_templates.add(formula_info['canonical_template'])
        self.original_to_canonical[formula_info['template']] = formula_info['canonical_template']
        
        # Создаем ключ для проверки дубликатов
        formula_key = f"{formula_info['canonical_template']}:{formula_info['left']}"
        self.processed_formulas.add(formula_key)
    
    def is_duplicate(self, canonical_template, left_part):
        """Проверяет, была ли уже обработана такая формула"""
        formula_key = f"{canonical_template}:{left_part}"
        return formula_key in self.processed_formulas
    
    def create_relations(self):
        """Создает отношения из всех уникальных канонических шаблонов"""
        relations_list = []
        
        for canonical_template in sorted(self.canonical_templates):
            if canonical_template.startswith("y="):
                relation = FormulaProcessor.create_relation_from_template(canonical_template)
                if relation:
                    relations_list.append(relation)
                    self.canonical_to_relation[canonical_template] = relation['shortName']
        
        return relations_list
    
    def get_relation_name(self, canonical_template):
        """Возвращает имя отношения по каноническому шаблону"""
        return self.canonical_to_relation.get(canonical_template)
    
    def get_all_formulas(self):
        """Возвращает все формулы"""
        return self.formulas
    
    def get_formulas_by_class(self, class_name):
        """Возвращает формулы для конкретного класса"""
        return [f for f in self.formulas if f['class'] == class_name]
    
    def clear(self):
        """Очищает реестр"""
        self.formulas.clear()
        self.canonical_templates.clear()
        self.template_to_relation.clear()
        self.canonical_to_relation.clear()
        self.original_to_canonical.clear()
        self.processed_formulas.clear()
