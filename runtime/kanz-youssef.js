/* Youssef Lab (2026-10-16): registry for draft components, styles and animations. Everything registered here is an
 * unapproved draft until Ahmed approves it; it is not used in final Kanz output until then.
 * Load after kanz-look.js / kanz-pace.js / kanz-3d.js.
 *
 *   K.lab.add("name", fn)      register a draft component: fn(parent, opts) -> element
 *   K.lab.use("name", parent, opts)   build it in a scene
 *   K.lab.style("name", css)   inject a named style block once; returns the <style> element
 *   K.lab.has("name")          true when a component is registered
 *
 * Document each addition in docs/YOUSSEF-LAB.md and library/youssef/manifest.json.
 */
(function () {
  const K = window.K;
  const reg = {}, styles = {};
  K.lab = {
    add(name, fn) { reg[name] = fn; return fn; },
    has: (name) => !!reg[name],
    use(name, parent, o = {}) {
      if (!reg[name]) throw new Error("Youssef Lab: component not registered: " + name);
      return reg[name](parent, o);
    },
    style(name, css) {
      if (styles[name]) return styles[name];
      const s = document.createElement("style");
      s.dataset.lab = name;
      s.textContent = css;
      document.head.appendChild(s);
      return (styles[name] = s);
    },
  };
})();
