#define _GNU_SOURCE
/* Pull icon, portrait, and loading-screen thumbnails out of a WoW client.

   Links LibWoW (MPQ through Mists, CASC from Warlords on). SpellIcon.dbc and
   ItemDisplayInfo.dbc supply the names on older clients. Later CASC roots
   often keep the BLP paths but drop the DBC names, so pass --names from an
   earlier extract, or --listfile (fdid;path) when the root has no names.
*/
#include "wow/wow.h"

#include <ctype.h>
#include <errno.h>
#include <png.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define MAX_EDGE_ICON 64u
#define MAX_EDGE_SHEET 256u

typedef struct {
    char *path;
    char *base;
    int   kind; /* 0 icon, 1 sheet, 2 screen */
} thumb;

static thumb  *g_items;
static size_t  g_n, g_cap;
static int     g_limit;

static void die(const char *what)
{
    fprintf(stderr, "%s: %s\n", what, strerror(errno));
    exit(1);
}

static char *xdup(const char *s)
{
    size_t n = strlen(s) + 1;
    char  *p = malloc(n);
    if (p == NULL) {
        die("malloc");
    }
    memcpy(p, s, n);
    return p;
}

static void basename_of(const char *path, char *out, size_t n)
{
    const char *slash = path;
    const char *p;
    size_t      len;
    for (p = path; *p; p++) {
        if (*p == '\\' || *p == '/') {
            slash = p + 1;
        }
    }
    snprintf(out, n, "%s", slash);
    len = strlen(out);
    if (len > 4 && strcasecmp(out + len - 4, ".blp") == 0) {
        out[len - 4] = 0;
    }
}

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

static int cmp_base(const void *a, const void *b)
{
    return strcasecmp(((const thumb *)a)->base, ((const thumb *)b)->base);
}

static void add_path(const char *path, int kind)
{
    char base[128];
    if (path == NULL || path[0] == 0) {
        return;
    }
    basename_of(path, base, sizeof base);
    if (base[0] == 0) {
        return;
    }
    if (g_n == g_cap) {
        g_cap = g_cap ? g_cap * 2 : 256;
        g_items = realloc(g_items, g_cap * sizeof *g_items);
        if (g_items == NULL) {
            die("realloc");
        }
    }
    g_items[g_n].path = xdup(path);
    g_items[g_n].base = xdup(base);
    g_items[g_n].kind = kind;
    g_n++;
}

static void unique_items(void)
{
    size_t i, w = 0;
    qsort(g_items, g_n, sizeof *g_items, cmp_base);
    for (i = 0; i < g_n; i++) {
        if (w > 0 && strcasecmp(g_items[w - 1].base, g_items[i].base) == 0) {
            free(g_items[i].path);
            free(g_items[i].base);
            continue;
        }
        g_items[w++] = g_items[i];
    }
    g_n = w;
}

static void add_icon_name(const char *name)
{
    char path[256];
    if (!icon_token(name)) {
        return;
    }
    snprintf(path, sizeof path, "Interface\\Icons\\%s.blp", name);
    add_path(path, 0);
}

static void add_client_path(const char *path)
{
    char   buf[512];
    size_t n;
    int    kind = 1;
    if (path == NULL) {
        return;
    }
    snprintf(buf, sizeof buf, "%s", path);
    n = strlen(buf);
    if (n > 4 && strcasecmp(buf + n - 4, ".blp") != 0) {
        if (n + 5 >= sizeof buf) {
            return;
        }
        memcpy(buf + n, ".blp", 5);
    }
    if (strstr(buf, "Icons") || strstr(buf, "ICONS")) {
        kind = 0;
    } else if (strstr(buf, "LoadingScreen")) {
        kind = 2;
    }
    add_path(buf, kind);
}

static int path_wanted(const char *path)
{
    if (path == NULL || strcasestr(path, ".blp") == NULL) {
        return 0;
    }
    return strcasestr(path, "\\Icons\\") != NULL || strcasestr(path, "/Icons/") != NULL
        || strcasestr(path, "CharacterCreate") != NULL
        || strcasestr(path, "LoadingScreen") != NULL;
}

static void load_names_file(const char *file)
{
    FILE *fp = fopen(file, "r");
    char  line[512];
    if (fp == NULL) {
        die(file);
    }
    while (fgets(line, sizeof line, fp)) {
        char *p = line;
        size_t n;
        while (*p == ' ' || *p == '\t') {
            p++;
        }
        n = strlen(p);
        while (n > 0 && (p[n - 1] == '\n' || p[n - 1] == '\r')) {
            p[--n] = 0;
        }
        if (p[0] == 0 || p[0] == '#') {
            continue;
        }
        if (strchr(p, '\\') || strchr(p, '/')) {
            add_client_path(p);
        } else {
            add_icon_name(p);
        }
    }
    fclose(fp);
}

static void load_listfile(wow_client *c, const char *file)
{
    FILE *fp;
    char  line[1024];
    wow_status st = wow_client_set_listfile(c, file);
    if (st != WOW_OK) {
        fprintf(stderr, "listfile: %s (%s)\n", wow_status_string(st), wow_last_detail());
        exit(1);
    }
    fp = fopen(file, "r");
    if (fp == NULL) {
        die(file);
    }
    while (fgets(line, sizeof line, fp)) {
        char *sep = strchr(line, ';');
        char *path;
        size_t n;
        if (sep == NULL) {
            sep = strchr(line, ',');
        }
        if (sep == NULL) {
            continue;
        }
        path = sep + 1;
        n = strlen(path);
        while (n > 0 && (path[n - 1] == '\n' || path[n - 1] == '\r')) {
            path[--n] = 0;
        }
        if (path_wanted(path)) {
            add_client_path(path);
        }
    }
    fclose(fp);
}

static void collect_dbc(wow_client *c)
{
    static const char *spell_icon[] = {
        "DBFilesClient/SpellIcon.dbc", "DBFilesClient\\SpellIcon.dbc", NULL
    };
    static const char *item_disp[] = {
        "DBFilesClient/ItemDisplayInfo.dbc", "DBFilesClient\\ItemDisplayInfo.dbc", NULL
    };
    static const char *loading[] = {
        "DBFilesClient/LoadingScreens.dbc", "DBFilesClient\\LoadingScreens.dbc", NULL
    };
    const char **cand;
    wow_blob    *b = NULL;
    wow_db      *db = NULL;
    uint32_t     row, rows, col, cols, u;
    const char  *s;

    for (cand = spell_icon; *cand; cand++) {
        if (wow_client_open_path(c, *cand, &b) == WOW_OK) {
            break;
        }
    }
    if (b != NULL && wow_db_open(b, NULL, &db) == WOW_OK && wow_db_col_count(db) >= 2) {
        rows = wow_db_row_count(db);
        for (row = 0; row < rows; row++) {
            if (wow_db_field_u32(db, row, 1, &u) != WOW_OK) {
                continue;
            }
            s = wow_db_string(db, u);
            if (s[0] && (strstr(s, "Icons") || strstr(s, "ICONS") || icon_token(s))) {
                if (strchr(s, '\\') || strchr(s, '/')) {
                    add_client_path(s);
                } else {
                    add_icon_name(s);
                }
            }
        }
        fprintf(stderr, "SpellIcon rows %u, queued %zu\n", rows, g_n);
        wow_db_close(db);
        db = NULL;
    }
    if (b) {
        wow_blob_destroy(b);
        b = NULL;
    }

    for (cand = item_disp; *cand; cand++) {
        if (wow_client_open_path(c, *cand, &b) == WOW_OK) {
            break;
        }
    }
    if (b != NULL && wow_db_open(b, NULL, &db) == WOW_OK && wow_db_col_count(db) > 5) {
        rows = wow_db_row_count(db);
        for (row = 0; row < rows; row++) {
            if (wow_db_field_u32(db, row, 5, &u) != WOW_OK) {
                continue;
            }
            add_icon_name(wow_db_string(db, u));
        }
        fprintf(stderr, "ItemDisplayInfo rows %u, queued %zu\n", rows, g_n);
        wow_db_close(db);
        db = NULL;
    }
    if (b) {
        wow_blob_destroy(b);
        b = NULL;
    }

    for (cand = loading; *cand; cand++) {
        if (wow_client_open_path(c, *cand, &b) == WOW_OK) {
            break;
        }
    }
    if (b != NULL && wow_db_open(b, NULL, &db) == WOW_OK) {
        rows = wow_db_row_count(db);
        cols = wow_db_col_count(db);
        for (row = 0; row < rows; row++) {
            for (col = 0; col < cols; col++) {
                if (wow_db_field_u32(db, row, col, &u) != WOW_OK) {
                    continue;
                }
                s = wow_db_string(db, u);
                if (strstr(s, "LoadingScreen") || (strstr(s, "Interface") && strstr(s, ".blp"))) {
                    add_client_path(s);
                }
            }
        }
        wow_db_close(db);
    }
    if (b) {
        wow_blob_destroy(b);
    }
}

static void collect_sheets(void)
{
    static const char *sheets[] = {
        "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Classes.blp",
        "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Races.blp",
        "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Factions.blp",
        NULL
    };
    int i;
    for (i = 0; sheets[i]; i++) {
        add_path(sheets[i], 1);
    }
}

static int ensure_dir(const char *path)
{
    char   tmp[1024];
    size_t len, i;
    snprintf(tmp, sizeof tmp, "%s", path);
    len = strlen(tmp);
    if (len == 0) {
        return -1;
    }
    for (i = 1; i < len; i++) {
        if (tmp[i] == '/') {
            tmp[i] = 0;
            if (mkdir(tmp, 0755) != 0 && errno != EEXIST) {
                return -1;
            }
            tmp[i] = '/';
        }
    }
    if (mkdir(tmp, 0755) != 0 && errno != EEXIST) {
        return -1;
    }
    return 0;
}

static void downscale(const uint8_t *src, uint32_t sw, uint32_t sh,
                      uint8_t *dst, uint32_t dw, uint32_t dh)
{
    uint32_t y, x, sy, sx;
    for (y = 0; y < dh; y++) {
        uint32_t y0 = y * sh / dh;
        uint32_t y1 = (y + 1) * sh / dh;
        if (y1 == y0) {
            y1 = y0 + 1;
        }
        for (x = 0; x < dw; x++) {
            uint32_t x0 = x * sw / dw;
            uint32_t x1 = (x + 1) * sw / dw;
            uint64_t acc[4] = {0, 0, 0, 0};
            uint32_t count = 0;
            if (x1 == x0) {
                x1 = x0 + 1;
            }
            for (sy = y0; sy < y1 && sy < sh; sy++) {
                for (sx = x0; sx < x1 && sx < sw; sx++) {
                    const uint8_t *p = src + ((size_t)sy * sw + sx) * 4;
                    acc[0] += p[0];
                    acc[1] += p[1];
                    acc[2] += p[2];
                    acc[3] += p[3];
                    count++;
                }
            }
            if (count == 0) {
                count = 1;
            }
            dst[((size_t)y * dw + x) * 4 + 0] = (uint8_t)(acc[0] / count);
            dst[((size_t)y * dw + x) * 4 + 1] = (uint8_t)(acc[1] / count);
            dst[((size_t)y * dw + x) * 4 + 2] = (uint8_t)(acc[2] / count);
            dst[((size_t)y * dw + x) * 4 + 3] = (uint8_t)(acc[3] / count);
        }
    }
}

static int write_png(const char *path, const uint8_t *rgba, uint32_t w, uint32_t h)
{
    FILE       *fp;
    png_structp png = NULL;
    png_infop   info = NULL;
    png_bytep  *rows = NULL;
    uint32_t    y;
    fp = fopen(path, "wb");
    if (fp == NULL) {
        return -1;
    }
    png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (png == NULL) {
        fclose(fp);
        return -1;
    }
    info = png_create_info_struct(png);
    if (info == NULL || setjmp(png_jmpbuf(png))) {
        png_destroy_write_struct(&png, &info);
        fclose(fp);
        free(rows);
        return -1;
    }
    png_init_io(png, fp);
    png_set_IHDR(png, info, w, h, 8, PNG_COLOR_TYPE_RGBA, PNG_INTERLACE_NONE,
                 PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
    png_write_info(png, info);
    rows = malloc(h * sizeof *rows);
    if (rows == NULL) {
        die("malloc");
    }
    for (y = 0; y < h; y++) {
        rows[y] = (png_bytep)(rgba + (size_t)y * w * 4);
    }
    png_write_image(png, rows);
    png_write_end(png, NULL);
    png_destroy_write_struct(&png, &info);
    free(rows);
    fclose(fp);
    return 0;
}

static int extract_one(wow_client *c, const thumb *t, const char *out_dir, FILE *manifest)
{
    wow_blob   *b = NULL;
    wow_blp    *blp = NULL;
    uint8_t    *rgba = NULL;
    uint8_t    *small = NULL;
    size_t      n = 0;
    uint32_t    w, h, dw, dh, max_edge;
    const char *folder;
    char        dest[1024];
    wow_status  st;

    st = wow_client_open_path(c, t->path, &b);
    if (st != WOW_OK) {
        return 0;
    }
    st = wow_blp_open(b, NULL, &blp);
    wow_blob_destroy(b);
    if (st != WOW_OK) {
        return 0;
    }
    st = wow_blp_decode_rgba(blp, &rgba, &n);
    w = wow_blp_width(blp);
    h = wow_blp_height(blp);
    wow_blp_close(blp);
    if (st != WOW_OK || rgba == NULL || w == 0 || h == 0) {
        wow_free(NULL, rgba);
        return 0;
    }
    max_edge = t->kind == 0 ? MAX_EDGE_ICON : MAX_EDGE_SHEET;
    dw = w;
    dh = h;
    if (w > max_edge || h > max_edge) {
        if (w >= h) {
            dw = max_edge;
            dh = h * max_edge / w;
        } else {
            dh = max_edge;
            dw = w * max_edge / h;
        }
        if (dw == 0) {
            dw = 1;
        }
        if (dh == 0) {
            dh = 1;
        }
        small = malloc((size_t)dw * dh * 4);
        if (small == NULL) {
            die("malloc");
        }
        downscale(rgba, w, h, small, dw, dh);
    }
    folder = t->kind == 0 ? "icons" : (t->kind == 2 ? "screens" : "ui");
    snprintf(dest, sizeof dest, "%s/%s", out_dir, folder);
    if (ensure_dir(dest) != 0) {
        die(dest);
    }
    snprintf(dest, sizeof dest, "%s/%s/%s.png", out_dir, folder, t->base);
    if (write_png(dest, small ? small : rgba, dw, dh) != 0) {
        fprintf(stderr, "png %s\n", dest);
    } else if (manifest) {
        fprintf(manifest, "%s\t%s\t%s/%s.png\n", folder, t->base, folder, t->base);
    }
    free(small);
    wow_free(NULL, rgba);
    return 1;
}

static void usage(const char *argv0)
{
    fprintf(stderr,
            "usage: %s <client-dir> <out-dir> [--names file] [--listfile file] [--limit n]\n",
            argv0);
}

int main(int argc, char **argv)
{
    wow_client *c = NULL;
    const char *names = NULL;
    const char *listfile = NULL;
    FILE       *manifest = NULL;
    FILE       *namefile = NULL;
    char        man_path[1024];
    char        names_path[1024];
    size_t      i;
    int         wrote = 0, missed = 0;
    wow_status  st;

    if (argc < 3) {
        usage(argv[0]);
        return 2;
    }
    for (i = 3; i < (size_t)argc; i++) {
        if (strcmp(argv[i], "--names") == 0 && i + 1 < (size_t)argc) {
            names = argv[++i];
        } else if (strcmp(argv[i], "--listfile") == 0 && i + 1 < (size_t)argc) {
            listfile = argv[++i];
        } else if (strcmp(argv[i], "--limit") == 0 && i + 1 < (size_t)argc) {
            g_limit = atoi(argv[++i]);
        } else {
            usage(argv[0]);
            return 2;
        }
    }
    st = wow_client_open(argv[1], NULL, &c);
    if (st != WOW_OK) {
        fprintf(stderr, "open %s: %s (%s)\n", argv[1], wow_status_string(st), wow_last_detail());
        return 1;
    }
    fprintf(stderr, "client build %u storage %s\n", wow_client_build(c),
            wow_client_storage(c) == WOW_STORAGE_CASC ? "casc" : "mpq");
    if (listfile) {
        load_listfile(c, listfile);
    }
    collect_dbc(c);
    collect_sheets();
    if (names) {
        load_names_file(names);
    }
    unique_items();
    fprintf(stderr, "queued %zu paths\n", g_n);
    if (ensure_dir(argv[2]) != 0) {
        die(argv[2]);
    }
    snprintf(man_path, sizeof man_path, "%s/manifest.tsv", argv[2]);
    snprintf(names_path, sizeof names_path, "%s/names.txt", argv[2]);
    manifest = fopen(man_path, "w");
    namefile = fopen(names_path, "w");
    if (manifest == NULL || namefile == NULL) {
        die("manifest");
    }
    fprintf(manifest, "kind\tname\tfile\n");
    for (i = 0; i < g_n; i++) {
        if (g_limit && wrote >= g_limit) {
            break;
        }
        if (extract_one(c, &g_items[i], argv[2], manifest)) {
            wrote++;
            fprintf(namefile, "%s\n", g_items[i].path);
            if (wrote % 500 == 0) {
                fprintf(stderr, "wrote %d\n", wrote);
            }
        } else {
            missed++;
        }
    }
    fclose(manifest);
    fclose(namefile);
    wow_client_close(c);
    fprintf(stderr, "wrote %d, missing %d, out %s\n", wrote, missed, argv[2]);
    return wrote == 0 ? 1 : 0;
}
