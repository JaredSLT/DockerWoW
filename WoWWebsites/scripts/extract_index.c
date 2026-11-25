/* Write spell-name and item-display indexes next to extracted thumbnails.
   spell-names.tsv: spell name <TAB> icon stem
   displays.tsv:    display id <TAB> icon stem
   Icon stems match static/img/client/<id>/icons/<stem>.png.
*/
#define _GNU_SOURCE
#include "wow/wow.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int icon_token(const char *s)
{
    size_t i, n;
    if (s == NULL) {
        return 0;
    }
    n = strlen(s);
    if (n < 3 || n > 80) {
        return 0;
    }
    for (i = 0; i < n; i++) {
        unsigned char c = (unsigned char)s[i];
        if (!(isalnum(c) || c == '_')) {
            return 0;
        }
    }
    return 1;
}

static const char *stem_from_path(const char *s, char *buf, size_t n)
{
    const char *base = s;
    const char *p;
    size_t len;
    for (p = s; *p; p++) {
        if (*p == '\\' || *p == '/') {
            base = p + 1;
        }
    }
    snprintf(buf, n, "%s", base);
    len = strlen(buf);
    if (len > 4 && strcasecmp(buf + len - 4, ".blp") == 0) {
        buf[len - 4] = 0;
    }
    return buf;
}

static wow_db *open_db(wow_client *c, const char *path)
{
    wow_blob *b = NULL;
    wow_db *db = NULL;
    if (wow_client_open_path(c, path, &b) != WOW_OK) {
        return NULL;
    }
    if (wow_db_open(b, NULL, &db) != WOW_OK) {
        wow_blob_destroy(b);
        return NULL;
    }
    wow_blob_destroy(b);
    return db;
}

/* SpellIcon column 0 is the id. WDBC has no separate id block, so
   wow_db_row_id() is only the row number. */
static char **load_icons(wow_db *db, uint32_t *out_n)
{
    uint32_t rows = wow_db_row_count(db);
    uint32_t i, id, off, cap = 1024;
    char **tab;
    char stem[128];
    *out_n = 0;
    tab = calloc(cap, sizeof *tab);
    if (tab == NULL) {
        return NULL;
    }
    for (i = 0; i < rows; i++) {
        if (wow_db_field_u32(db, i, 0, &id) != WOW_OK) {
            continue;
        }
        if (wow_db_field_u32(db, i, 1, &off) != WOW_OK) {
            continue;
        }
        stem_from_path(wow_db_string(db, off), stem, sizeof stem);
        if (!icon_token(stem) || id >= 200000) {
            continue;
        }
        if (id >= cap) {
            uint32_t ncap = cap;
            while (id >= ncap) {
                ncap *= 2;
            }
            tab = realloc(tab, ncap * sizeof *tab);
            if (tab == NULL) {
                return NULL;
            }
            memset(tab + cap, 0, (ncap - cap) * sizeof *tab);
            cap = ncap;
        }
        tab[id] = strdup(stem);
        if (id + 1 > *out_n) {
            *out_n = id + 1;
        }
    }
    return tab;
}

/* A field is a real string only when its offset lands on a string-block
   boundary. Mid-string offsets are suffixes ("…Fireball") and are not names. */
static int string_start(const wow_db *db, uint32_t off)
{
    const char *prev;
    if (off == 0) {
        return 1;
    }
    prev = wow_db_string(db, off - 1);
    return prev[0] == 0;
}

static int name_like(const char *s)
{
    size_t n, i, letters = 0;
    if (s == NULL) {
        return 0;
    }
    n = strlen(s);
    if (n < 3 || n > 48) {
        return 0;
    }
    if (strchr(s, '\\') || strchr(s, '/')) {
        return 0;
    }
    for (i = 0; i < n; i++) {
        unsigned char c = (unsigned char)s[i];
        if (isalpha(c)) {
            letters++;
        } else if (!(c == ' ' || c == '\'' || c == '-' || c == ':' || c == ',' || c == '.' || c == '(' || c == ')')) {
            return 0;
        }
    }
    return letters >= 3;
}

int main(int argc, char **argv)
{
    wow_client *c = NULL;
    wow_db *icons_db, *spell_db, *disp;
    char **icons = NULL;
    uint32_t icon_n = 0, rows, cols, r, col, off, icon_col = 0, name_col = 0;
    uint32_t found_name = 0, found_icon = 0;
    FILE *spells, *displays;
    char spell_path[1024], disp_path[1024];

    if (argc < 3) {
        fprintf(stderr, "usage: %s <client> <out-dir>\n", argv[0]);
        return 2;
    }
    if (wow_client_open(argv[1], NULL, &c) != WOW_OK) {
        fprintf(stderr, "open failed: %s\n", wow_last_detail());
        return 1;
    }
    icons_db = open_db(c, "DBFilesClient/SpellIcon.dbc");
    if (icons_db == NULL) {
        icons_db = open_db(c, "DBFilesClient\\SpellIcon.dbc");
    }
    spell_db = open_db(c, "DBFilesClient/Spell.dbc");
    if (spell_db == NULL) {
        spell_db = open_db(c, "DBFilesClient\\Spell.dbc");
    }
    snprintf(spell_path, sizeof spell_path, "%s/spell-names.tsv", argv[2]);
    snprintf(disp_path, sizeof disp_path, "%s/displays.tsv", argv[2]);
    spells = fopen(spell_path, "w");
    displays = fopen(disp_path, "w");
    if (spells == NULL || displays == NULL) {
        perror("open tsv");
        return 1;
    }
    fprintf(spells, "name\ticon\n");
    fprintf(displays, "display\ticon\n");

    if (icons_db && spell_db) {
        icons = load_icons(icons_db, &icon_n);
        rows = wow_db_row_count(spell_db);
        cols = wow_db_col_count(spell_db);
        {
            int fire_row = -1, hero_row = -1;
            for (r = 0; r < rows && (fire_row < 0 || hero_row < 0); r++) {
                for (col = 0; col < cols; col++) {
                    const char *s;
                    if (wow_db_field_u32(spell_db, r, col, &off) != WOW_OK) {
                        continue;
                    }
                    s = wow_db_string(spell_db, off);
                    if (!string_start(spell_db, off)) {
                        continue;
                    }
                    if (fire_row < 0 && strcmp(s, "Fireball") == 0) {
                        fire_row = (int)r;
                        name_col = col;
                        found_name = 1;
                    }
                    if (hero_row < 0 && strcmp(s, "Heroic Strike") == 0) {
                        hero_row = (int)r;
                        if (!found_name) {
                            name_col = col;
                            found_name = 1;
                        }
                    }
                }
            }
            if (fire_row >= 0) {
                for (col = 0; col < cols; col++) {
                    uint32_t fv = 0;
                    if (wow_db_field_u32(spell_db, (uint32_t)fire_row, col, &fv) != WOW_OK) {
                        continue;
                    }
                    if (fv == 0 || fv >= icon_n || icons[fv] == NULL) {
                        continue;
                    }
                    if (strcasestr(icons[fv], "FlameBolt")) {
                        icon_col = col;
                        found_icon = 1;
                        break;
                    }
                }
            }
        }
        fprintf(stderr, "spell name col %u (%s) icon col %u (%s) rows %u\n",
                name_col, found_name ? "found" : "missing",
                icon_col, found_icon ? "found" : "missing", rows);
        if (found_name && found_icon) {
            for (r = 0; r < rows; r++) {
                const char *s;
                uint32_t id = 0;
                char stem[128];
                if (wow_db_field_u32(spell_db, r, name_col, &off) != WOW_OK) {
                    continue;
                }
                s = wow_db_string(spell_db, off);
                if (!string_start(spell_db, off) || !name_like(s)) {
                    continue;
                }
                if (wow_db_field_u32(spell_db, r, icon_col, &id) != WOW_OK) {
                    continue;
                }
                if (id == 0 || id >= icon_n || icons[id] == NULL) {
                    continue;
                }
                snprintf(stem, sizeof stem, "%s", icons[id]);
                if (strcmp(stem, "Temp") == 0) {
                    continue;
                }
                /* TSV: reject tabs in names. */
                if (strchr(s, '\t') || strchr(s, '\n')) {
                    continue;
                }
                fprintf(spells, "%s\t%s\n", s, stem);
            }
        }
    } else {
        fprintf(stderr, "no Spell.dbc on this client\n");
    }

    disp = open_db(c, "DBFilesClient/ItemDisplayInfo.dbc");
    if (disp == NULL) {
        disp = open_db(c, "DBFilesClient\\ItemDisplayInfo.dbc");
    }
    if (disp && wow_db_col_count(disp) > 5) {
        rows = wow_db_row_count(disp);
        for (r = 0; r < rows; r++) {
            const char *s;
            char stem[128];
            if (wow_db_field_u32(disp, r, 5, &off) != WOW_OK) {
                continue;
            }
            s = wow_db_string(disp, off);
            stem_from_path(s, stem, sizeof stem);
            if (!icon_token(stem)) {
                continue;
            }
            uint32_t did = 0;
            if (wow_db_field_u32(disp, r, 0, &did) != WOW_OK || did == 0) {
                continue;
            }
            fprintf(displays, "%u\t%s\n", did, stem);
        }
        fprintf(stderr, "displays %u\n", rows);
    } else {
        fprintf(stderr, "no ItemDisplayInfo.dbc\n");
    }

    fclose(spells);
    fclose(displays);
    wow_client_close(c);
    return 0;
}
