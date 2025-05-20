document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.tomselect').forEach(function(select) {
        new TomSelect(select, {
            create: false,
            persist: false,
            maxItems: null,
            plugins: ['remove_button']
        });
    });
});