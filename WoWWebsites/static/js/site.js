function toggleMenu(btn) {
  var menu = btn.parentNode;
  var open = menu.classList.contains("open");
  menu.classList.toggle("open", !open);
  menu.classList.toggle("closed", open);
  btn.setAttribute("aria-expanded", open ? "false" : "true");
}

document.addEventListener("click", function (ev) {
  var btn = ev.target.closest(".menu-btn");
  if (btn) toggleMenu(btn);
});

function initTalents(maxPoints) {
  var buttons = Array.prototype.slice.call(document.querySelectorAll(".talent"));
  var ptsEl = document.getElementById("pts");
  var buildEl = document.getElementById("build");
  var byId = {};
  buttons.forEach(function (b) {
    byId[b.getAttribute("data-i")] = b;
  });
  function rankOf(b) {
    return Number(b.querySelector("[data-rank]").textContent.split("/")[0]);
  }
  function maxOf(b) {
    return Number(b.getAttribute("data-max"));
  }
  function rowOf(b) {
    return Number(b.getAttribute("data-row"));
  }
  function treeOf(b) {
    return b.getAttribute("data-tree");
  }
  function spent() {
    return buttons.reduce(function (n, b) {
      return n + rankOf(b);
    }, 0);
  }
  function treePoints(tree, skip) {
    return buttons.reduce(function (n, b) {
      if (treeOf(b) !== tree || b === skip) return n;
      return n + rankOf(b);
    }, 0);
  }
  function canSpend(b) {
    var cur = rankOf(b);
    if (cur >= maxOf(b) || !(maxPoints > 0) || spent() >= maxPoints) return false;
    var tree = treeOf(b);
    if (treePoints(tree, null) < 5 * rowOf(b)) return false;
    var req = b.getAttribute("data-requires");
    if (req) {
      var reqBtn = byId[req];
      if (!reqBtn || rankOf(reqBtn) < maxOf(reqBtn)) return false;
    }
    return true;
  }
  function canUnspend(b) {
    var cur = rankOf(b);
    if (!(cur > 0)) return false;
    var tree = treeOf(b);
    var newPoints = treePoints(tree, b) + (cur - 1);
    var i, other, r;
    for (i = 0; i < buttons.length; i++) {
      other = buttons[i];
      if (treeOf(other) !== tree) continue;
      r = other === b ? cur - 1 : rankOf(other);
      if (r > 0 && newPoints < 5 * rowOf(other)) return false;
    }
    if (cur - 1 < maxOf(b)) {
      var id = b.getAttribute("data-i");
      for (i = 0; i < buttons.length; i++) {
        other = buttons[i];
        if (treeOf(other) !== tree) continue;
        r = other === b ? cur - 1 : rankOf(other);
        if (other.getAttribute("data-requires") === id && r > 0) return false;
      }
    }
    return true;
  }
  function setRank(b, rank) {
    b.querySelector("[data-rank]").textContent = rank + "/" + maxOf(b);
  }
  function paint() {
    var left = maxPoints - spent();
    if (ptsEl) ptsEl.textContent = String(left);
    var digits = buttons.map(function (b) {
      return b.querySelector("[data-rank]").textContent.split("/")[0];
    }).join("");
    if (buildEl) buildEl.textContent = digits;
    if (window.history && window.history.replaceState) {
      var url = location.pathname + (digits.replace(/0+$/, "") ? "?build=" + digits : "");
      history.replaceState(null, "", url);
    }
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (ev.button === 2 || ev.shiftKey) {
        if (canUnspend(b)) setRank(b, rankOf(b) - 1);
      } else if (canSpend(b)) {
        setRank(b, rankOf(b) + 1);
      }
      paint();
    });
    b.addEventListener("contextmenu", function (ev) {
      ev.preventDefault();
      if (canUnspend(b)) setRank(b, rankOf(b) - 1);
      paint();
    });
  });
  paint();
}

window.initTalents = initTalents;
