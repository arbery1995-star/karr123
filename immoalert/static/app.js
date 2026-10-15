(() => {
  const RADII = [5, 10, 20, 30, 50, 100, 150, 200];
  const $ = (id) => document.getElementById(id);
  const num = (id) => parseFloat(($(id).value || "0").replace(",", ".")) || 0;
  const eur = (v) => v.toLocaleString("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

  // Umkreis-Slider rastet auf die von den Portalen unterstützten Radien ein
  const slider = $("radius-slider"), hidden = $("radius"), out = $("radius-out");
  const start = RADII.findIndex((r) => r >= parseInt(hidden.value, 10));
  slider.value = start === -1 ? RADII.length - 1 : start;
  const syncRadius = () => {
    hidden.value = RADII[slider.value];
    out.textContent = `${hidden.value} km`;
  };
  slider.addEventListener("input", syncRadius);
  syncRadius();

  // Live-Beispielrechnung – dieselbe Formel wie immoalert/cashflow.py
  const calc = () => {
    const price = num("ex_price"), size = num("ex_size");
    const rent = size * num("rent_per_sqm");
    const loan = Math.max(0, price * (1 + num("closing_pct") / 100) - num("equity"));
    const rate = loan * (num("interest_pct") + num("repayment_pct")) / 100 / 12;
    const costs = rent * num("costs_pct") / 100;
    const cf = rent - rate - costs;
    const target = num("min_cashflow");

    $("o_rent").textContent = `+ ${eur(rent)}`;
    $("o_rate").textContent = `− ${eur(rate)}`;
    $("o_costs").textContent = `− ${eur(costs)}`;
    $("o_cf").textContent = eur(cf);
    $("o_cf").className = cf >= 0 ? "pos" : "neg";
    $("o_loan").textContent = eur(loan);
    $("o_yield").textContent = price ? `${(rent * 12 / price * 100).toFixed(1).replace(".", ",")} %` : "–";

    const v = $("o_verdict");
    if (cf >= target) {
      v.textContent = `✓ Dieses Objekt würden wir dir schicken (≥ ${eur(target)}).`;
      v.className = "verdict ok";
    } else {
      const maxPrice = findMaxPrice(size, target);
      v.textContent = maxPrice > 0
        ? `✗ Zu teuer für ${eur(target)} Überschuss – lohnt sich bis ca. ${eur(maxPrice)}.`
        : `✗ Mit diesen Annahmen nicht erreichbar.`;
      v.className = "verdict no";
    }
  };

  // Höchster Kaufpreis, bei dem der Ziel-Überschuss noch erreicht wird (geschlossen gelöst)
  const findMaxPrice = (size, target) => {
    const rent = size * num("rent_per_sqm");
    const net = rent * (1 - num("costs_pct") / 100) - target;
    const factor = (num("interest_pct") + num("repayment_pct")) / 100 / 12;
    if (net <= 0) return 0;
    if (factor === 0) return Infinity;
    return Math.floor(((net / factor) + num("equity")) / (1 + num("closing_pct") / 100) / 1000) * 1000;
  };

  document.getElementById("alert-form").addEventListener("input", calc);
  calc();
})();
