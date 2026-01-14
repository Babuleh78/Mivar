from lxml import etree
import uuid

def create_class(parent, short_name="Одна модель", is_nested=False, class_id=None):
    """Создает класс с указанным именем внутри родительского элемента"""
    if class_id is None:
        class_id = str(uuid.uuid4())
    
    if is_nested:
        id_str = class_id  
    else:
        id_str = f"{{{class_id}}}"
    
    new_class = etree.SubElement(parent, "class",
                              id=id_str,
                              shortName=short_name)
    
    new_class.text = "\n"
    
    # Создаем стандартные элементы
    parameters = etree.SubElement(new_class, "parameters")
    rules = etree.SubElement(new_class, "rules")
    constraints = etree.SubElement(new_class, "constraints")
    classes_elem = etree.SubElement(new_class, "classes")
    
    # Устанавливаем tail
    parameters.tail = "\n"
    rules.tail = "\n"
    constraints.tail = "\n"
    
    if is_nested:
        # Для вложенных классов - пустой classes
        classes_elem.tail = "\n"
    else:
        # Для основного класса - возможно добавление вложенных
        classes_elem.text = "\n" 
        classes_elem.tail = "\n"
    
    new_class.tail = "\n" if parent.tag == "classes" else "\n"
    
    return classes_elem  # Возвращаем элемент classes

def create_xml():
    model = etree.Element("model", 
                          id=f"{{{str(uuid.uuid4())}}}",
                          shortName="Одна модель",
                          formatXmlVersion="2.0",
                          description="Model 1")
    
    model.text = "\n"
    
    # Создаем основной класс
    main_class_elem = etree.SubElement(model, "class",
                                       id=f"{{{str(uuid.uuid4())}}}",
                                       shortName="Одна модель")
    main_class_elem.text = "\n"
    
    # Создаем элементы основного класса
    parameters = etree.SubElement(main_class_elem, "parameters")
    rules = etree.SubElement(main_class_elem, "rules")
    constraints = etree.SubElement(main_class_elem, "constraints")
    classes_elem = etree.SubElement(main_class_elem, "classes")
    
    parameters.tail = "\n"
    rules.tail = "\n"
    constraints.tail = "\n"
    classes_elem.text = "\n"  # Перенос перед вложенными классами
    classes_elem.tail = "\n"
    
    # Добавляем вложенные классы (в обратном порядке, как в примере)
    # Вложенный класс 2 (первый в XML)
    nested2_classes = create_class(classes_elem, "Вложенный класс 2", 
                                   is_nested=True, 
                                   class_id="0366d483-03ae-4551-a37a-8f9716bece7a")
    
    # Вложенный класс 1 (второй в XML)
    nested1_classes = create_class(classes_elem, "Вложенный класс 1", 
                                   is_nested=True, 
                                   class_id="a12eb6d1-ed39-40fc-b225-62f8c7888716")
    
    # Закрывающий tail для основного класса
    main_class_elem.tail = "\n"
    
    # Добавляем relations
    relations = etree.SubElement(model, "relations")
    relations.tail = "\n"
    
    # Создаем и сохраняем дерево
    tree = etree.ElementTree(model)
    
    with open("physics_model.xml", "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", pretty_print=False)
    
    print("XML файл создан: physics_model.xml")
    
    xml_str = etree.tostring(model, encoding="utf-8", pretty_print=False).decode('utf-8')
    print("Содержимое XML:")
    print(xml_str)
    
    return tree

if __name__ == "__main__":
    create_xml()
