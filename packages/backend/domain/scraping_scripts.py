"""JavaScript snippets for Playwright execution."""

EXTRACT_FORM_FIELDS_JS = """
() => {
    const fields = [];
    const form = document.querySelector('form') || document.body;

    function getLabel(el) {
        if (el.id) {
            const lbl = document.querySelector('label[for="' + el.id + '"]');
            if (lbl) return lbl.innerText.trim();
        }
        const parent = el.closest('label');
        if (parent) {
            const clone = parent.cloneNode(true);
            clone.querySelectorAll('input,select,textarea').forEach(c => c.remove());
            return clone.innerText.trim();
        }
        return el.getAttribute('aria-label')
            || el.getAttribute('placeholder')
            || el.getAttribute('name')
            || '';
    }

    function selectorFor(el) {
        // MEDIUM: Prefer stable selectors (id, name) over nth-of-type
        if (el.id) return '#' + el.id;
        if (el.name):
            return el.tagName.toLowerCase() + '[name="' + el.name + '"]'
        # Try data attributes as fallback
        if el.getAttribute('data-field-id'):
            return (
                el.tagName.toLowerCase() + 
                '[data-field-id="' + el.getAttribute('data-field-id') + '"]'
            )
        if el.getAttribute('data-testid'):
            return el.tagName.toLowerCase() + '[data-testid="' + el.getAttribute('data-testid') + '"]'
        // Last resort: nth-of-type (fragile, may break with DOM changes)
        // WARNING: This selector is fragile and may break if form structure changes
        const siblings = Array.from(form.querySelectorAll(el.tagName.toLowerCase()));
        const idx = siblings.indexOf(el);
        return el.tagName.toLowerCase() + ':nth-of-type(' + (idx + 1) + ')';
    }

    form.querySelectorAll('input, select, textarea').forEach(el => {
        const type = el.tagName.toLowerCase() === 'select' ? 'select'
                   : el.tagName.toLowerCase() === 'textarea' ? 'textarea'
                   : (el.getAttribute('type') || 'text');
        if (['hidden', 'submit', 'button', 'image', 'reset'].includes(type)) return;

        const entry = {
            selector: selectorFor(el),
            label: getLabel(el),
            type: type,
            required: el.required || el.getAttribute('aria-required') === 'true',
            options: null
        };

        if (el.tagName.toLowerCase() === 'select') {
            entry.options = Array.from(el.options).map(o => ({
                value: o.value,
                text: o.text.trim()
            })).filter(o => o.value !== '');
        }

        if (type === 'radio') {
            const name = el.getAttribute('name');
            if (name) {
                const radios = form.querySelectorAll('input[type="radio"][name="' + name + '"]');
                entry.options = Array.from(radios).map(r => ({
                    value: r.value,
                    text: (function(rel) {
                        const p = rel.closest('label');
                        if (p) {
                            const c = p.cloneNode(true);
                            c.querySelectorAll('input').forEach(x => x.remove());
                            return c.innerText.trim();
                        }
                        return rel.value;
                    })(r)
                }));
            }
        }

        fields.push(entry);
    });

    return fields;
}
"""
