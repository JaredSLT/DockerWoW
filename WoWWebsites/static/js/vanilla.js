/* Overrides for the November 2006 community scripts.
   Flash is not used. Search and the PvP rail stay on this host.
   window.VANILLA_PVP is a list of {name, kills} set by the page. */
var MM_FlashCanPlay = false;

function searchCall() {
  var box = document.getElementById("searchBox");
  var sel = document.getElementById("searchType");
  var q = box ? box.value : "";
  var type = sel ? sel.value : "site";
  window.location.href = "/wow/search?q=" + encodeURIComponent(q) + "&searchType=" + encodeURIComponent(type);
  return false;
}

function xmlDataLoad(xmlSource, xslSource, container, aSync, loader) {
  var rows = window.VANILLA_PVP || [];
  var faction = String(xmlSource || "").indexOf("faction=h") >= 0 ? "Horde" : "Alliance";
  var html = '<p style="margin:4px 8px;font:bold 11px Arial,sans-serif">' + faction + "</p>";
  if (!rows.length) {
    html += '<p style="margin:4px 8px;font:11px Arial,sans-serif">No honor data on this realm yet.</p>';
  } else {
    html += '<table style="width:190px;font:11px Arial,sans-serif;color:#000">';
    var i;
    for (i = 0; i < rows.length && i < 10; i++) {
      var row = rows[i];
      html += "<tr><td><a href=\"/wow/pvp/rankings\">" +
        row.name.replace(/[&<>"]/g, function (ch) {
          return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;"}[ch];
        }) + "</a></td><td>" + row.kills + "</td></tr>";
    }
    html += "</table>";
  }
  var el = document.getElementById(container);
  if (el) el.innerHTML = html;
  if (loader) {
    var box = document.getElementById(loader);
    if (box) box.style.display = "none";
  }
}
