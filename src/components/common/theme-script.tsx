/**
 * Blocking inline script that applies the theme class to <html> before first paint.
 * Reads the Zustand persist key ("ui-theme") from localStorage so the resolved
 * class is set before the browser paints, preventing FOUC.
 *
 * Must be rendered inside <head> in the root layout (Server Component).
 */
export function ThemeScript() {
  const script = `
(function(){
  try {
    var raw = localStorage.getItem('ui-theme');
    var theme = 'system';
    if (raw) {
      var parsed = JSON.parse(raw);
      if (parsed && parsed.state && parsed.state.theme) {
        theme = parsed.state.theme;
      }
    }
    var resolved = theme;
    if (theme === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    }
    document.documentElement.classList.add(resolved);
    document.documentElement.style.colorScheme = resolved;
  } catch (e) {}
})();`;

  return (
    <script
      dangerouslySetInnerHTML={{ __html: script }}
      // Intentionally no async/defer — must block rendering
    />
  );
}
