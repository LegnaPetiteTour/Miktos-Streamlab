#!/bin/bash
# Fix common markdown linting issues in DAY1 files

for file in DAY1_*.md; do
    echo "Fixing $file..."
    
    # Add language specifier to code blocks without one
    perl -i -0pe 's/\n```\n(?!python|bash|text|json|javascript|typescript)/\n```text\n/g' "$file"
    
    # Add blank line before ### headings when missing
    perl -i -pe 's/^([^\n#])$/\1\n/ if $prev =~ /^[^#]/ && /^###/; $prev = $_' "$file"
    
    # Add blank line after lists before headings
    perl -i -0pe 's/(\n- [^\n]+\n)(\n###)/\1\n\2/g' "$file"
    perl -i -0pe 's/(\n\d+\. [^\n]+\n)(\n###)/\1\n\2/g' "$file"
    
    # Add blank line before lists after headings/bold text
    perl -i -0pe 's/(\*\*[^*]+\*\*:\n)([-\d])/\1\n\2/g' "$file"
done

echo "✅ Markdown fixes applied"
