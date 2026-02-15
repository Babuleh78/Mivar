import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import webbrowser
from excel_processor import ExcelProcessor


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel to MIVAR XML Converter")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Центрируем окно
        self.center_window(1000, 800)
        
        self.input_file = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_filename = tk.StringVar(value="MIVAR.xml")
        
        self.processor = ExcelProcessor()
        
        self.create_widgets()
        
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        # Главный фрейм с отступами
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame, 
            text="Excel to MIVAR XML Converter", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        file_frame = ttk.LabelFrame(main_frame, text="Выбор файла", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="Excel файл:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Обзор...", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        
        output_frame = ttk.LabelFrame(main_frame, text="Настройки вывода", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Папка вывода:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(output_frame, text="Обзор...", command=self.browse_output).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(output_frame, text="Имя XML файла:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(output_frame, textvariable=self.output_filename, width=50).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Фрейм для кнопок действий
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            action_frame, 
            text="Обработать файл", 
            command=self.process_file,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame, 
            text="Очистить поля", 
            command=self.clear_fields,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Фрейм для информации о создателе
        self.create_author_info(main_frame)
        
        # Фрейм для лога
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Текстовое поле для лога с прокруткой
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Статус бар
        self.status_bar = ttk.Label(
            self.root, 
            text="Готов к работе", 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_author_info(self, parent):
        author_frame = ttk.LabelFrame(parent, text="О создателе", padding="10")
        author_frame.pack(fill=tk.X, pady=(0, 10))
        
        inner_frame = ttk.Frame(author_frame)
        inner_frame.pack(fill=tk.X)
        
        # Информация об авторе
        ttk.Label(
            inner_frame, 
            text="Разработчик: Денис Маркин", 
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Label(
            inner_frame, 
            text="Версия: 0.0.1", 
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Label(
            inner_frame, 
            text="Назначение: Конвертер Excel файлов в MIVAR XML формат", 
            font=("Arial", 9),
            wraplength=600
        ).pack(anchor=tk.W, pady=2)
        
        # Фрейм для ссылок
        links_frame = ttk.Frame(inner_frame)
        links_frame.pack(anchor=tk.W, pady=5)
        
        github_link = ttk.Label(
            links_frame, 
            text="GitHub: https://github.com/Babuleh78/Mivar/tree/main",
            font=("Arial", 9, "underline"),
            foreground="blue",
            cursor="hand2"
        )
        github_link.pack(side=tk.LEFT, padx=(0, 20))
        github_link.bind("<Button-1>", lambda e: self.open_link("https://github.com/Babuleh78/Mivar/tree/main"))
        
        # Ссылка на email
        email_link = ttk.Label(
            links_frame, 
            text="Email: jdbdbsbbfdh@gmail.com",
            font=("Arial", 9, "underline"),
            foreground="blue",
            cursor="hand2"
        )
        email_link.pack(side=tk.LEFT)
        email_link.bind("<Button-1>", lambda e: self.open_link("mailto:jdbdbsbbfdh@gmail.com"))
    
    def open_link(self, url):
        webbrowser.open(url)
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            self.log(f"Выбран входной файл: {filename}")
    
    def browse_output(self):
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения результатов"
        )
        if folder:
            self.output_folder.set(folder)
            self.log(f"Выбрана папка вывода: {folder}")
    
    def clear_fields(self):
        """Очищает все поля ввода"""
        self.input_file.set("")
        self.output_folder.set("")
        self.output_filename.set("MIVAR.xml")
        self.log_text.delete(1.0, tk.END)
        self.log("Поля очищены")
        self.update_status("Готов к работе")
    
    def log(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, message):
        """Обновляет статус бар"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def process_file(self):
        """Обрабатывает выбранный файл"""
        
        # Проверяем, выбран ли входной файл
        if not self.input_file.get():
            messagebox.showerror("Ошибка", "Пожалуйста, выберите входной Excel файл")
            return
        
        # Проверяем, существует ли файл
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Ошибка", "Входной файл не существует")
            return
        
        # Проверяем расширение файла
        if not self.input_file.get().lower().endswith(('.xlsx', '.xls')):
            if not messagebox.askyesno("Предупреждение", 
                                       "Файл может не быть Excel файлом. Продолжить?"):
                return
        
        # Проверяем имя выходного файла
        if not self.output_filename.get():
            messagebox.showerror("Ошибка", "Пожалуйста, укажите имя выходного XML файла")
            return
        
        # Проверяем, существует ли папка вывода (если указана)
        if self.output_folder.get() and not os.path.exists(self.output_folder.get()):
            try:
                os.makedirs(self.output_folder.get())
                self.log(f"Создана папка: {self.output_folder.get()}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку вывода: {e}")
                return
        
        # Очищаем лог
        self.log_text.delete(1.0, tk.END)
        
        # Блокируем кнопки во время обработки
        self.update_status("Обработка...")
        self.root.config(cursor="watch")
        
        try:
            # Обрабатываем файл
            self.log("=" * 50)
            self.log("НАЧАЛО ОБРАБОТКИ")
            self.log("=" * 50)
            self.log(f"Входной файл: {self.input_file.get()}")
            self.log(f"Папка вывода: {self.output_folder.get() or 'текущая директория'}")
            self.log(f"Имя XML файла: {self.output_filename.get()}")
            self.log("-" * 50)
            
            # Запускаем обработку
            stats = self.processor.process(
                input_file=self.input_file.get(),
                output_folder=self.output_folder.get() or None,
                xml_filename=self.output_filename.get()
            )
            
            # Выводим результаты
            self.log("-" * 50)
            self.log("РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
            self.log(f"✅ Отношений создано: {stats['relations']}")
            self.log(f"✅ Классов создано: {stats['classes']}")
            self.log(f"✅ Правил создано: {stats['rules']}")
            self.log(f"✅ Формул обработано: {stats['formulas']}")
            self.log("-" * 50)
            self.log(f"📁 Обработанный Excel: {stats['excel_path']}")
            self.log(f"📁 XML файл: {stats['xml_path']}")
            self.log("=" * 50)
            self.log("ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
            
            self.update_status("Обработка завершена")
            
            # Показываем сообщение об успехе
            messagebox.showinfo(
                "Успех", 
                f"Обработка завершена успешно!\n\n"
                f"Создано отношений: {stats['relations']}\n"
                f"Создано классов: {stats['classes']}\n"
                f"Создано правил: {stats['rules']}\n\n"
                f"XML файл сохранен в:\n{stats['xml_path']}"
            )
            
        except Exception as e:
            self.log(f"❌ ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Произошла ошибка при обработке:\n{str(e)}")
            self.update_status("Ошибка при обработке")
        
        finally:
            # Разблокируем кнопки
            self.root.config(cursor="")


def main():
    """Точка входа в программу"""
    root = tk.Tk()
    app = Application(root)
    
    # Обработка закрытия окна
    def on_closing():
        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Запускаем главный цикл
    root.mainloop()


if __name__ == "__main__":
    main()
