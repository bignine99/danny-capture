import codecs
import re

file_path = r'c:\Users\cho\Desktop\Temp\05 Code\251123_NNHomepage\src\data\solutions.ts'

with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

new_solution = """    {
        id: 'solution-danny-capture',
        title: 'Danny Capture Pro',
        description: '강력하고 직관적인 화면 캡처 및 편집 도구',
        description2: 'AI 에이전트 작업 및 기술 문서 작성에 최적화된 화면 캡처 프로그램. 단축키 한 번으로 캡처, 편집, 클립보드 복사까지 원스톱으로 제공하며 고화질 이미지 처리와 다중 모니터 환경을 완벽 지원합니다.',
        href: '/downloads/DannyCapture_Setup.exe',
        icon: 'Image',
        external: true,
        category: 'General',
        hasSpecialEffect: true,
        isNew: true,
    },
"""

content = content.replace('export const simpleSolutions: Solution[] = [\n', 'export const simpleSolutions: Solution[] = [\n' + new_solution)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)

print('Updated solutions.ts')
