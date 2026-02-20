"""
Render round-robin algorithm diagrams for the triage scheduler.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUT_DIR = '/home/user/triage-scheduler/docs/diagrams'
os.makedirs(OUT_DIR, exist_ok=True)

# Shared colors
BLUE = '#4a90d9'
ORANGE = '#e07b53'
GREEN = '#5ba55b'
RED = '#d9534f'
YELLOW = '#f0ad4e'
GRAY = '#cccccc'
LIGHT_BLUE = '#dce9f5'
LIGHT_ORANGE = '#fbe4d8'
WHITE = '#ffffff'
DARK = '#333333'

MEMBERS = ['Alice (0)', 'Bob (1)', 'Carol (2)', 'Dave (3)', 'Eve (4)', 'Frank (5)']
SHORT = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank']


def diagram_1_ring():
    """The circular member ring with dual pointers."""
    fig, ax = plt.subplots(1, 1, figsize=(9, 9))
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.5, 2.5)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(WHITE)

    ax.set_title('Diagram 1: The Round-Robin Ring\n(6 team members, 2 independent pointers)',
                 fontsize=16, fontweight='bold', pad=20)

    n = len(MEMBERS)
    radius = 1.5
    angles = [np.pi/2 - 2*np.pi*i/n for i in range(n)]  # start at top, go clockwise

    xs = [radius * np.cos(a) for a in angles]
    ys = [radius * np.sin(a) for a in angles]

    # Draw connecting arrows (ring)
    for i in range(n):
        j = (i + 1) % n
        dx = xs[j] - xs[i]
        dy = ys[j] - ys[i]
        length = np.sqrt(dx**2 + dy**2)
        # Shorten to avoid overlapping with circles
        shrink = 0.35
        ax.annotate('', xy=(xs[j] - shrink*dx/length, ys[j] - shrink*dy/length),
                     xytext=(xs[i] + shrink*dx/length, ys[i] + shrink*dy/length),
                     arrowprops=dict(arrowstyle='->', color='#888888', lw=1.5))

    # Draw member circles
    for i in range(n):
        circle = plt.Circle((xs[i], ys[i]), 0.32, facecolor=LIGHT_BLUE, edgecolor=BLUE, linewidth=2)
        ax.add_patch(circle)
        ax.text(xs[i], ys[i], SHORT[i], ha='center', va='center', fontsize=11, fontweight='bold')
        ax.text(xs[i], ys[i] - 0.18, f'order={i}', ha='center', va='center', fontsize=8, color='#666')

    # Pointer A -> Alice (index 0)
    ptr_a_angle = angles[0]
    ptr_a_x = (radius + 0.8) * np.cos(ptr_a_angle)
    ptr_a_y = (radius + 0.8) * np.sin(ptr_a_angle)
    ax.annotate('', xy=(xs[0], ys[0] + 0.35),
                xytext=(ptr_a_x, ptr_a_y + 0.15),
                arrowprops=dict(arrowstyle='->', color=BLUE, lw=2.5))
    ax.text(ptr_a_x, ptr_a_y + 0.35, 'Pointer A\n(App A)', ha='center', va='center',
            fontsize=11, fontweight='bold', color=BLUE,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=LIGHT_BLUE, edgecolor=BLUE))

    # Pointer B -> Bob (index 1)
    ptr_b_angle = angles[1]
    ptr_b_x = (radius + 0.85) * np.cos(ptr_b_angle)
    ptr_b_y = (radius + 0.85) * np.sin(ptr_b_angle)
    ax.annotate('', xy=(xs[1] + 0.25, ys[1] + 0.2),
                xytext=(ptr_b_x + 0.1, ptr_b_y + 0.05),
                arrowprops=dict(arrowstyle='->', color=ORANGE, lw=2.5))
    ax.text(ptr_b_x + 0.1, ptr_b_y + 0.25, 'Pointer B\n(App B)', ha='center', va='center',
            fontsize=11, fontweight='bold', color=ORANGE,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=LIGHT_ORANGE, edgecolor=ORANGE))

    # Legend
    ax.text(0, -2.2, 'Each pointer advances independently through the ring.\n'
            'Pointer A tracks last App A assignee. Pointer B tracks last App B assignee.',
            ha='center', va='center', fontsize=10, style='italic', color='#555')

    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/01_ring.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 01_ring.png')


def diagram_2_weekly_rotation():
    """Week-by-week rotation table showing 6 weeks."""
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.axis('off')
    fig.patch.set_facecolor(WHITE)

    ax.set_title('Diagram 2: Week-by-Week Rotation (6 Members, 2 Apps)\n'
                 'Showing pointer advancement and cool-down skips',
                 fontsize=15, fontweight='bold', pad=20)

    weeks = [
        {'week': 'Week 1', 'ptr_a_before': -1, 'ptr_a_after': 0, 'ptr_b_before': -1, 'ptr_b_after': 1,
         'app_a': 'Alice (0)', 'app_b': 'Bob (1)', 'skips': 'None (first week)'},
        {'week': 'Week 2', 'ptr_a_before': 0, 'ptr_a_after': 2, 'ptr_b_before': 1, 'ptr_b_after': 3,
         'app_a': 'Carol (2)', 'app_b': 'Dave (3)',
         'skips': 'Bob skipped for A (did B last wk)\nAlice skipped for B (did A last wk)'},
        {'week': 'Week 3', 'ptr_a_before': 2, 'ptr_a_after': 4, 'ptr_b_before': 3, 'ptr_b_after': 5,
         'app_a': 'Eve (4)', 'app_b': 'Frank (5)',
         'skips': 'Dave skipped for A (did B last wk)\nCarol skipped for B (did A last wk)'},
        {'week': 'Week 4', 'ptr_a_before': 4, 'ptr_a_after': 0, 'ptr_b_before': 5, 'ptr_b_after': 1,
         'app_a': 'Alice (0)', 'app_b': 'Bob (1)',
         'skips': 'Frank skipped for A (did B last wk)\nEve skipped for B (did A last wk)\nPointers wrap around!'},
        {'week': 'Week 5', 'ptr_a_before': 0, 'ptr_a_after': 2, 'ptr_b_before': 1, 'ptr_b_after': 3,
         'app_a': 'Carol (2)', 'app_b': 'Dave (3)',
         'skips': 'Cycle repeats identically'},
        {'week': 'Week 6', 'ptr_a_before': 2, 'ptr_a_after': 4, 'ptr_b_before': 3, 'ptr_b_after': 5,
         'app_a': 'Eve (4)', 'app_b': 'Frank (5)',
         'skips': 'Cycle repeats identically'},
    ]

    col_labels = ['Week', 'Ptr A\n(before→after)', 'App A\nAssigned', 'Ptr B\n(before→after)',
                  'App B\nAssigned', 'Cool-down Skips']

    cell_text = []
    cell_colors = []
    for w in weeks:
        row = [
            w['week'],
            f"{w['ptr_a_before']} → {w['ptr_a_after']}",
            w['app_a'],
            f"{w['ptr_b_before']} → {w['ptr_b_after']}",
            w['app_b'],
            w['skips'],
        ]
        cell_text.append(row)
        colors = [WHITE, LIGHT_BLUE, LIGHT_BLUE, LIGHT_ORANGE, LIGHT_ORANGE, '#fff8f0']
        cell_colors.append(colors)

    table = ax.table(cellText=cell_text, colLabels=col_labels,
                     cellColours=cell_colors, loc='center', cellLoc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 2.2)

    # Style header
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(DARK)
        cell.set_text_props(color=WHITE, fontweight='bold')

    # Highlight wrap-around row
    for j in range(len(col_labels)):
        cell = table[4, j]  # row 4 = Week 4 (1-indexed with header)
        cell.set_edgecolor(GREEN)
        cell.set_linewidth(2)

    # Add note at bottom
    ax.text(0.5, -0.02, 'Pattern: each member is assigned once every 3 weeks. '
            'No one does back-to-back duty across apps. Green border = pointer wrap-around.',
            ha='center', va='top', fontsize=10, style='italic', color='#555',
            transform=ax.transAxes)

    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/02_weekly_rotation.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 02_weekly_rotation.png')


def diagram_3_algorithm_flowchart():
    """Algorithm decision flowchart."""
    fig, ax = plt.subplots(figsize=(12, 16))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 20)
    ax.axis('off')
    fig.patch.set_facecolor(WHITE)

    ax.set_title('Diagram 3: Algorithm Flowchart\n'
                 'How assignments are calculated for a single week',
                 fontsize=15, fontweight='bold', pad=20)

    def draw_box(x, y, w, h, text, color=LIGHT_BLUE, edge=BLUE, fontsize=9, bold=False):
        rect = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                        boxstyle='round,pad=0.15',
                                        facecolor=color, edgecolor=edge, linewidth=1.5)
        ax.add_patch(rect)
        weight = 'bold' if bold else 'normal'
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
                fontweight=weight, wrap=True)

    def draw_diamond(x, y, w, h, text, color='#fff3cd', edge=YELLOW):
        diamond = plt.Polygon([(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)],
                              facecolor=color, edgecolor=edge, linewidth=1.5)
        ax.add_patch(diamond)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5, fontweight='bold')

    def draw_arrow(x1, y1, x2, y2, label='', color='#555'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx + 0.15, my, label, fontsize=8, color=color, fontweight='bold')

    # Step 1: Start
    draw_box(6, 19.2, 4, 0.7, 'START: Need assignments for Week W', GREEN, GREEN, bold=True)

    # Step 2: Init
    draw_box(6, 18, 5.5, 0.8,
             'Load active members (sorted by rotation_order)\n'
             'Derive pointer_a and pointer_b from last assignments',
             LIGHT_BLUE, BLUE)
    draw_arrow(6, 18.85, 6, 18.4)

    # Step 3: Start App A
    draw_box(6, 16.8, 4.5, 0.7, 'FIND CANDIDATE FOR APP A\nAdvance from pointer_a + 1',
             LIGHT_BLUE, BLUE, bold=True)
    draw_arrow(6, 17.6, 6, 17.15)

    # Decision: Available?
    draw_diamond(6, 15.7, 3.6, 1.1, 'Member\navailable?')
    draw_arrow(6, 16.45, 6, 16.25)

    # No - unavailable
    draw_box(9.5, 15.7, 2.2, 0.6, 'SKIP\n(on vacation)', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 15.7, 8.4, 15.7, 'No', RED)
    draw_arrow(9.5, 15.1, 6, 15.1)  # loop back - goes down then left
    ax.annotate('', xy=(6, 15.2), xytext=(6, 15.1),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.2))

    # Yes - check cooldown
    draw_diamond(6, 14.2, 3.6, 1.1, 'Did App B\nlast week?')
    draw_arrow(6, 15.15, 6, 14.75, 'Yes')

    # Cooldown violation
    draw_box(9.5, 14.2, 2.2, 0.6, 'SKIP\n(cool-down)', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 14.2, 8.4, 14.2, 'Yes', RED)

    # Assign App A
    draw_box(6, 13, 3.5, 0.7, 'ASSIGN TO APP A\nUpdate pointer_a', LIGHT_BLUE, BLUE, bold=True)
    draw_arrow(6, 13.65, 6, 13.35, 'No')

    # Separator
    ax.plot([1, 11], [12.3, 12.3], '--', color=GRAY, lw=1)
    ax.text(6, 12.45, '─── Now find App B ───', ha='center', fontsize=9, color='#888')

    # Step: Start App B
    draw_box(6, 11.5, 4.5, 0.7, 'FIND CANDIDATE FOR APP B\nAdvance from pointer_b + 1',
             LIGHT_ORANGE, ORANGE, bold=True)
    draw_arrow(6, 12.3, 6, 11.85)

    # Decision: Available?
    draw_diamond(6, 10.4, 3.6, 1.1, 'Member\navailable?')
    draw_arrow(6, 11.15, 6, 10.95)

    draw_box(9.5, 10.4, 2.2, 0.6, 'SKIP\n(on vacation)', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 10.4, 8.4, 10.4, 'No', RED)

    # Check cooldown B
    draw_diamond(6, 9.0, 3.6, 1.1, 'Did App A\nlast week?')
    draw_arrow(6, 9.85, 6, 9.55, 'Yes')

    draw_box(9.5, 9.0, 2.2, 0.6, 'SKIP\n(cool-down)', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 9.0, 8.4, 9.0, 'Yes', RED)

    # Check same person
    draw_diamond(6, 7.6, 3.6, 1.1, 'Same as\nApp A\nthis week?')
    draw_arrow(6, 8.45, 6, 8.15, 'No')

    draw_box(9.5, 7.6, 2.2, 0.6, 'SKIP\n(already used)', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 7.6, 8.4, 7.6, 'Yes', RED)

    # Assign App B
    draw_box(6, 6.4, 3.5, 0.7, 'ASSIGN TO APP B\nUpdate pointer_b', LIGHT_ORANGE, ORANGE, bold=True)
    draw_arrow(6, 7.05, 6, 6.75, 'No')

    # Done
    draw_box(6, 5.3, 4, 0.7, 'DONE: Return both assignments', GREEN, GREEN, bold=True)
    draw_arrow(6, 6.05, 6, 5.65)

    # Fallback note
    draw_box(6, 4.0, 8, 1.0,
             'FALLBACK: If no valid candidate found (pool too small),\n'
             'relax the cool-down constraint and retry.\n'
             'If still impossible (< 2 available), raise SchedulingError.',
             '#fff3cd', YELLOW, fontsize=9)

    fig.savefig(f'{OUT_DIR}/03_algorithm_flowchart.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 03_algorithm_flowchart.png')


def diagram_4_cooldown_visual():
    """Visual showing cool-down in action across 4 weeks."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    fig.patch.set_facecolor(WHITE)
    fig.suptitle('Diagram 4: Cool-Down in Action\n'
                 'Who gets skipped and why (4 consecutive weeks)',
                 fontsize=14, fontweight='bold', y=1.02)

    weeks_data = [
        {'title': 'Week 1', 'app_a': 0, 'app_b': 1, 'skip_a': [], 'skip_b': [], 'unavail': []},
        {'title': 'Week 2', 'app_a': 2, 'app_b': 3, 'skip_a': [1], 'skip_b': [0], 'unavail': []},
        {'title': 'Week 3', 'app_a': 4, 'app_b': 5, 'skip_a': [3], 'skip_b': [2], 'unavail': []},
        {'title': 'Week 4', 'app_a': 0, 'app_b': 1, 'skip_a': [5], 'skip_b': [4], 'unavail': []},
    ]

    for idx, (ax, wd) in enumerate(zip(axes, weeks_data)):
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(-0.5, 6.5)
        ax.axis('off')
        ax.set_title(wd['title'], fontsize=13, fontweight='bold')

        for i, name in enumerate(SHORT):
            y = 5.5 - i
            color = WHITE
            edge = '#ccc'
            marker = ''

            if i == wd['app_a']:
                color = LIGHT_BLUE
                edge = BLUE
                marker = '  ← App A'
            elif i == wd['app_b']:
                color = LIGHT_ORANGE
                edge = ORANGE
                marker = '  ← App B'
            elif i in wd['skip_a']:
                color = '#fce4e4'
                edge = RED
                marker = '  ✗ cool-down'
            elif i in wd['skip_b']:
                color = '#fce4e4'
                edge = RED
                marker = '  ✗ cool-down'
            elif i in wd['unavail']:
                color = GRAY
                edge = '#999'
                marker = '  ✗ vacation'

            rect = mpatches.FancyBboxPatch((0, y - 0.3), 1.1, 0.6,
                                            boxstyle='round,pad=0.08',
                                            facecolor=color, edgecolor=edge, linewidth=1.5)
            ax.add_patch(rect)
            ax.text(0.55, y, name, ha='center', va='center', fontsize=10, fontweight='bold')
            if marker:
                mcolor = BLUE if 'App A' in marker else (ORANGE if 'App B' in marker else RED)
                ax.text(1.2, y, marker, ha='left', va='center', fontsize=8, color=mcolor,
                        fontweight='bold')

    # Legend
    legend_items = [
        (LIGHT_BLUE, BLUE, 'Assigned to App A'),
        (LIGHT_ORANGE, ORANGE, 'Assigned to App B'),
        ('#fce4e4', RED, 'Skipped (cool-down)'),
        (WHITE, '#ccc', 'Available / idle'),
    ]

    fig.subplots_adjust(bottom=0.15)
    for i, (fc, ec, label) in enumerate(legend_items):
        x = 0.15 + i * 0.2
        rect = mpatches.FancyBboxPatch((x, 0.02), 0.03, 0.04,
                                        boxstyle='round,pad=0.005',
                                        facecolor=fc, edgecolor=ec, linewidth=1.5,
                                        transform=fig.transFigure)
        fig.patches.append(rect)
        fig.text(x + 0.04, 0.04, label, fontsize=9, va='center')

    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/04_cooldown_visual.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 04_cooldown_visual.png')


def diagram_5_exception_handling():
    """What happens when someone is on vacation."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor(WHITE)
    fig.suptitle('Diagram 5: Exception Handling (Vacation)\n'
                 'Week 3 — Carol is unavailable',
                 fontsize=14, fontweight='bold', y=1.02)

    # Left: Normal week 3
    ax = axes[0]
    ax.set_xlim(-0.5, 3)
    ax.set_ylim(-0.5, 7)
    ax.axis('off')
    ax.set_title('Normal Week 3\n(no exceptions)', fontsize=12, fontweight='bold', color=GREEN)

    normal = [(0, 'Alice', WHITE, '#ccc', ''),
              (1, 'Bob', WHITE, '#ccc', ''),
              (2, 'Carol', WHITE, '#ccc', ''),
              (3, 'Dave', '#fce4e4', RED, 'skip: did B wk2'),
              (4, 'Eve', LIGHT_BLUE, BLUE, 'APP A'),
              (5, 'Frank', LIGHT_ORANGE, ORANGE, 'APP B')]

    # Reverse so index 0 is at top
    for rot_order, name, color, edge, note in normal:
        y = 5.5 - rot_order
        rect = mpatches.FancyBboxPatch((0.2, y - 0.3), 1.2, 0.6,
                                        boxstyle='round,pad=0.08',
                                        facecolor=color, edgecolor=edge, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(0.8, y, name, ha='center', va='center', fontsize=10, fontweight='bold')
        if note:
            ncolor = BLUE if 'APP A' in note else (ORANGE if 'APP B' in note else RED)
            ax.text(1.55, y, note, ha='left', va='center', fontsize=9, color=ncolor, fontweight='bold')

    # Right: Exception week 3 (Carol on vacation)
    ax = axes[1]
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(-0.5, 7)
    ax.axis('off')
    ax.set_title('Week 3 with Carol on Vacation\n(algorithm adapts)', fontsize=12, fontweight='bold', color=ORANGE)

    exception = [(0, 'Alice', WHITE, '#ccc', ''),
                 (1, 'Bob', WHITE, '#ccc', ''),
                 (2, 'Carol', GRAY, '#999', 'VACATION'),
                 (3, 'Dave', '#fce4e4', RED, 'skip: did B wk2'),
                 (4, 'Eve', LIGHT_BLUE, BLUE, 'APP A'),
                 (5, 'Frank', LIGHT_ORANGE, ORANGE, 'APP B')]

    for rot_order, name, color, edge, note in exception:
        y = 5.5 - rot_order
        rect = mpatches.FancyBboxPatch((0.2, y - 0.3), 1.2, 0.6,
                                        boxstyle='round,pad=0.08',
                                        facecolor=color, edgecolor=edge, linewidth=1.5)
        ax.add_patch(rect)
        style = 'italic' if note == 'VACATION' else 'normal'
        ax.text(0.8, y, name, ha='center', va='center', fontsize=10, fontweight='bold',
                style=style)
        if note:
            ncolor = '#999' if 'VACATION' in note else (
                BLUE if 'APP A' in note else (ORANGE if 'APP B' in note else RED))
            ax.text(1.55, y, note, ha='left', va='center', fontsize=9, color=ncolor, fontweight='bold')

    # Annotation showing the algorithm thought process
    ax.text(0.2, -0.3,
            'App A: ptr at 2 → try Carol → VACATION → try Dave → cool-down → try Eve ✓\n'
            'App B: ptr at 3 → try Eve → same as App A → try Frank ✓',
            fontsize=9, color='#555', va='top', style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#f9f9f9', edgecolor='#ddd'))

    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/05_exception_handling.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 05_exception_handling.png')


def diagram_6_graceful_degradation():
    """Small pool: cool-down relaxed."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    fig.patch.set_facecolor(WHITE)
    fig.suptitle('Diagram 6: Graceful Degradation (Only 3 Members)\n'
                 'Cool-down must be relaxed when the pool is too small',
                 fontsize=14, fontweight='bold', y=1.02)

    small_members = ['Alice', 'Bob', 'Carol']

    scenarios = [
        {
            'title': 'Week 1\n(Normal)',
            'data': [('Alice', LIGHT_BLUE, BLUE, 'APP A'),
                     ('Bob', LIGHT_ORANGE, ORANGE, 'APP B'),
                     ('Carol', WHITE, '#ccc', '')],
            'note': 'Normal assignment',
            'note_color': GREEN,
        },
        {
            'title': 'Week 2\n(Normal)',
            'data': [('Alice', '#fce4e4', RED, 'skip: did A wk1'),
                     ('Bob', '#fce4e4', RED, 'skip: did B wk1'),
                     ('Carol', LIGHT_BLUE, BLUE, 'APP A')],
            'note': 'App A: Carol ✓\nApp B: Alice? skip (cool-down)\n→ Bob? skip (cool-down)\n→ NO VALID CANDIDATE!',
            'note_color': RED,
        },
        {
            'title': 'Week 2\n(Cool-down relaxed)',
            'data': [('Alice', LIGHT_ORANGE, ORANGE, 'APP B ⚠'),
                     ('Bob', WHITE, '#ccc', ''),
                     ('Carol', LIGHT_BLUE, BLUE, 'APP A')],
            'note': 'Cool-down relaxed for App B.\nAlice assigned despite doing\nApp A last week.\n⚠ Warning logged.',
            'note_color': YELLOW,
        },
    ]

    for ax, sc in zip(axes, scenarios):
        ax.set_xlim(-0.5, 3.5)
        ax.set_ylim(-1.5, 4)
        ax.axis('off')
        ax.set_title(sc['title'], fontsize=12, fontweight='bold')

        for i, (name, color, edge, note) in enumerate(sc['data']):
            y = 2.5 - i
            rect = mpatches.FancyBboxPatch((0.2, y - 0.3), 1.2, 0.6,
                                            boxstyle='round,pad=0.08',
                                            facecolor=color, edgecolor=edge, linewidth=1.5)
            ax.add_patch(rect)
            ax.text(0.8, y, name, ha='center', va='center', fontsize=10, fontweight='bold')
            if note:
                ncolor = BLUE if 'APP A' in note else (
                    ORANGE if 'APP B' in note else RED)
                ax.text(1.55, y, note, ha='left', va='center', fontsize=8.5,
                        color=ncolor, fontweight='bold')

        ax.text(0.2, -0.8, sc['note'], fontsize=9, color=sc['note_color'], va='top',
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#f9f9f9', edgecolor=sc['note_color']))

    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/06_graceful_degradation.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 06_graceful_degradation.png')


def diagram_7_fairness():
    """Bar chart showing assignment distribution over 12 weeks."""
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(WHITE)

    ax.set_title('Diagram 7: Fairness Over 12 Weeks\n'
                 'Every member gets equal duty — 2 assignments each per 6-week cycle',
                 fontsize=14, fontweight='bold', pad=15)

    # Over 12 weeks with 6 members: each person gets App A twice and App B twice
    members = SHORT
    app_a_counts = [2, 0, 2, 0, 2, 0]  # Alice, Carol, Eve do App A
    app_b_counts = [0, 2, 0, 2, 0, 2]  # Bob, Dave, Frank do App B

    # Actually with the pattern: Alice does A wk1,4,7,10 = 4 times in 12 weeks
    # Wait, let me recalculate for 12 weeks:
    # Wk1: A=Alice, B=Bob; Wk2: A=Carol, B=Dave; Wk3: A=Eve, B=Frank
    # Wk4: A=Alice, B=Bob; ... repeats every 3 weeks
    # In 12 weeks: each person assigned 4 times total (always same app)
    app_a_counts = [4, 0, 4, 0, 4, 0]
    app_b_counts = [0, 4, 0, 4, 0, 4]

    x = np.arange(len(members))
    width = 0.35

    bars1 = ax.bar(x - width/2, app_a_counts, width, label='App A', color=BLUE, edgecolor='white')
    bars2 = ax.bar(x + width/2, app_b_counts, width, label='App B', color=ORANGE, edgecolor='white')

    ax.set_ylabel('Number of Assignments', fontsize=11)
    ax.set_xlabel('Team Members', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(members, fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for bar in bars1:
        if bar.get_height() > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(int(bar.get_height())), ha='center', fontsize=10, fontweight='bold')
    for bar in bars2:
        if bar.get_height() > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(int(bar.get_height())), ha='center', fontsize=10, fontweight='bold')

    ax.text(0.5, -0.18,
            'Note: With the basic dual-pointer algorithm, odd-indexed members always get App B\n'
            'and even-indexed always get App A. Total duty is equal (4 each over 12 weeks).\n'
            'To rotate across apps, the pointers can be offset periodically.',
            ha='center', va='top', fontsize=9, style='italic', color='#555',
            transform=ax.transAxes)

    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/07_fairness.png', dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f'Saved 07_fairness.png')


if __name__ == '__main__':
    diagram_1_ring()
    diagram_2_weekly_rotation()
    diagram_3_algorithm_flowchart()
    diagram_4_cooldown_visual()
    diagram_5_exception_handling()
    diagram_6_graceful_degradation()
    diagram_7_fairness()
    print(f'\nAll diagrams saved to {OUT_DIR}/')
