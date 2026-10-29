def run():
    # 1. Update topic-detail-view.tsx
    path1 = 'src/components/courses/topic-detail-view.tsx'
    with open(path1, 'r', encoding='utf-8') as f:
        c1 = f.read()

    if 'MathText' not in c1:
        c1 = 'import { MathText } from "@/components/ui/math-text";\n' + c1
        c1 = c1.replace('{sq.text}', '<MathText content={sq.text} />')
        with open(path1, 'w', encoding='utf-8') as f:
            f.write(c1)
        print('Updated', path1)

    # 2. Update question-card.tsx
    path2 = 'src/components/ui/question-card.tsx'
    with open(path2, 'r', encoding='utf-8') as f:
        c2 = f.read()

    if 'MathText' not in c2:
        c2 = 'import { MathText } from "@/components/ui/math-text";\n' + c2
        c2 = c2.replace('{question.text}', '<MathText content={question.text} />')
        with open(path2, 'w', encoding='utf-8') as f:
            f.write(c2)
        print('Updated', path2)

if __name__ == '__main__':
    run()
