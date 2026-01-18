import pandas as pd
import re
from sympy import symbols, solve, Eq, sympify
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

class FormulaCreator:
    def solve_for_all_variables(self, formula_str):
        if not formula_str or not isinstance(formula_str, str):
            return []
        
        # Извлекаем все переменные
        formula_str = formula_str.replace(" ", "").replace("^", "**")
        variables = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', formula_str))
        
        if '=' not in formula_str:
            return []
        
        left_str, right_str = formula_str.split('=', 1)
        
        # Создаем символы для всех переменных
        syms = symbols(' '.join(variables))
        var_dict = {str(sym): sym for sym in syms}
        
        try:
            left_expr = sympify(left_str, locals=var_dict)
            right_expr = sympify(right_str, locals=var_dict)
            equation = Eq(left_expr, right_expr)
            
            results = []
            for var in variables:
                try:
                    solution = solve(equation, var_dict[var])
                    if solution:
                        for sol in solution:
                            result_str = str(sol).replace("**", "^")
                            results.append(f"{var} = {result_str}")
                except:
                    continue
            
            return results
        except Exception as e:
            print(f"Ошибка при обработке формулы '{formula_str}': {e}")
            return []

    def process_excel_by_column(self, input_file, output_file=None):
        if output_file is None:
            output_file = input_file.replace('.xlsx', '_transformed.xlsx')
        
        wb = load_workbook(input_file)
        ws = wb.active

        max_row = ws.max_row
        max_col = ws.max_column
        
        for col in range(1, max_col + 1):
            col_data = []
            col_letter = get_column_letter(col)
            
            for row in range(1, max_row + 1):
                cell_value = ws[f"{col_letter}{row}"].value
                if cell_value:
                    col_data.append(str(cell_value))
                else:
                    col_data.append(None)
            
            processed_data = []
            for item in col_data:
                if item and '=' in item:
                    processed_data.append(item)
                    transformations = self.solve_for_all_variables(item)
                    processed_data.extend(transformations)
                else:
                    processed_data.append(item)
            
            for idx, value in enumerate(processed_data, start=1):
                ws[f"{col_letter}{idx}"].value = value
        
        wb.save(output_file)
        print(f"Результат сохранен в: {output_file}")
        return output_file
