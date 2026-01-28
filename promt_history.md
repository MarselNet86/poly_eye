1. (claude sonnet 4.5) Проанализируйте мой код, я хочу чтобы вы его перевели в веб интерфейс. В нашем веб приложении не требуется выгрузка в excel поэтому мы опустим этот блок. Над дизайном не паримся, используем пока что голый html. Твоя задача описать мне код цельными файлами, чтобы я его мог потом вставить в проект. В django у меня уже есть приложение analyzer давай всю работу будем проводить там

Стек технологий - django/alpine.js/htmx.

2. (antigravity) заполни файл gitignore в соотвествии с моим проектом

3. (monkey brain activate) Ищем референс, мне понравился этот - https://dribbble.com/shots/23602689-Hublot-Online-Shop

4. (google ai studio - gemeni 3 pro) У меня есть файлы html без UI UX. Я хочу чтобы мы проанализировали картинку image.png и использовали такой дизайн код. Для описания дизайна используйте Tailwind
Мой сайт должен выглядить так: Сверху минималистичный header, где слева будет располагаться текст xDaimon ~ PolyEYE. По контенту пусть слева будет располагаться блок с шагами (скругленный), а справа основной блок с контентом (также скругленный)
    4.1 Пусть текст везде будет тонким. Обводка у блоков должна быть черная и тонкая. В header оставьте только текст POLYeye, справа у header уберите статус и выпадающий список, добавьте у header тонкий горизонтальный разделитель соотвествием с дизайном 

5. (antigravity) Тебе необходимо проанализировать код с папки @polyeye-trade-analyzer и перевести его в один единый файл index.html с сохранением всей логики и дизайна 
    5.1 Окей, но после того как я выбираю маркет на этапе SEARCH, у меня возникает ошибка и я не могу приступить к следующему этапу

    analyzer/:439 Uncaught TypeError: Cannot read properties of undefined (reading '$data')
        at HTMLInputElement.<anonymous> (analyzer/:439:63)
    (anonymous)	@	analyzer/:439

6. (antigravity) Нужно исправть следующие моменты:
    1) Иконка стрелки должна быть всегда черной при наведении или при клике

    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" data-lucide="arrow-right" aria-hidden="true" class="lucide lucide-arrow-right"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>

    2) left sider bar должен находиться на одной высоте с основным блоком, из-за отступов он смещен вниз относительно основного блока

    3) Resolution - не имеет смысла, нам не нужно знать как закрылась сделка

    4) из-за этого блока образуется пустное пространство после текста Performance <div id="analysis-loading" class="htmx-indicator w-full h-64 flex items-center justify-center">
                                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-black"></div>
                            </div>

    5) Мы должны иметь возможность кликнуть по миниатиюре Position Analysis чтобы увидеть полную картинку

    6.1 Давай подумаем шаг за шагом и проанализируем код. Когда я нажимаю на маркет ничего не происходит меня не перекидывает к дальнейшему этапу
