"""
Render round-robin algorithm diagrams for the triage scheduler.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), 'diagrams')
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
            'Pointer A tracks last App A assignee. Pointer B tracks last App B assignee.\n'
            'KEY RULE: Vacation skips do NOT advance the pointer. Cool-down skips DO.',
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
    draw_box(9.5, 15.7, 2.8, 0.7, 'SKIP (vacation)\nPointer does NOT advance', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 15.7, 8.1, 15.7, 'No', RED)
    draw_arrow(9.5, 15.05, 6, 15.05)  # loop back - goes down then left
    ax.annotate('', xy=(6, 15.15), xytext=(6, 15.05),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.2))

    # Yes - check cooldown
    draw_diamond(6, 14.2, 3.6, 1.1, 'Did App B\nlast week?')
    draw_arrow(6, 15.15, 6, 14.75, 'Yes')

    # Cooldown violation
    draw_box(9.5, 14.2, 2.8, 0.7, 'SKIP (cool-down)\nPointer DOES advance', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 14.2, 8.1, 14.2, 'Yes', RED)

    # Assign App A
    draw_box(6, 13, 4.5, 0.8, 'ASSIGN TO APP A\nAdvance pointer_a (unless vacation\nsubstitute — then pointer holds)',
             LIGHT_BLUE, BLUE, bold=True)
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

    draw_box(9.5, 10.4, 2.8, 0.7, 'SKIP (vacation)\nPointer does NOT advance', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 10.4, 8.1, 10.4, 'No', RED)

    # Check cooldown B
    draw_diamond(6, 9.0, 3.6, 1.1, 'Did App A\nlast week?')
    draw_arrow(6, 9.85, 6, 9.55, 'Yes')

    draw_box(9.5, 9.0, 2.8, 0.7, 'SKIP (cool-down)\nPointer DOES advance', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 9.0, 8.1, 9.0, 'Yes', RED)

    # Check same person
    draw_diamond(6, 7.6, 3.6, 1.1, 'Same as\nApp A\nthis week?')
    draw_arrow(6, 8.45, 6, 8.15, 'No')

    draw_box(9.5, 7.6, 2.2, 0.6, 'SKIP\n(already used)', '#fce4e4', RED, fontsize=8)
    draw_arrow(7.8, 7.6, 8.4, 7.6, 'Yes', RED)

    # Assign App B
    draw_box(6, 6.4, 4.5, 0.8, 'ASSIGN TO APP B\nAdvance pointer_b (unless vacation\nsubstitute — then pointer holds)',
             LIGHT_ORANGE, ORANGE, bold=True)
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
    """Option C: Pointer holds position on vacation. 4-week scenario.

    Correct scenario: Carol is at ring position 2. After Bob (pos 1) is assigned
    App A in Week 2, Ptr A sits at position 1. Week 3's search starts at pos 2
    (Carol) — her natural turn. Since she's on vacation, the pointer HOLDS at
    position 1 (just before Carol) and a substitute is found. This continues until
    Carol returns, at which point she gets her deferred assignment.

    Trace (Ptr A only; Ptr B advances normally):
      Week 2: Bob assigned App A → Ptr A at 1 (Bob).
      Week 3: start = pos 2 (Carol) → VACATION → HOLD. Dave cooldown, Eve subs.
              Ptr A stays at 1. Ptr B (at 3/Dave) → Frank gets App B.
      Week 4: start = pos 2 (Carol) → VACATION → HOLD (re-armed). Dave subs.
              Alice gets App B. Ptr A stays at 1.
      Week 5: start = pos 2 (Carol) → AVAILABLE → Carol assigned ★. Ptr A → 2.
              Bob gets App B.
    """
    fig, axes = plt.subplots(1, 4, figsize=(20, 8))
    fig.patch.set_facecolor(WHITE)
    fig.suptitle('Diagram 5: Vacation Handling — Pointer Holds Position (Option C)\n'
                 'Carol is on vacation Weeks 3-4. Her natural turn (pos 2) is held. She is assigned when she returns.',
                 fontsize=14, fontweight='bold', y=1.0)

    PURPLE = '#8e6fad'
    LIGHT_PURPLE = '#ede4f5'

    weeks_data = [
        {
            'title': 'Week 2 (normal)',
            'subtitle': 'Sets baseline — Carol is next',
            'members': [
                ('Alice', '#fce4e4', RED, 'skip: did A wk1'),
                ('Bob',   LIGHT_BLUE, BLUE, 'APP A'),
                ('Carol', WHITE, '#ccc', ''),
                ('Dave',  LIGHT_ORANGE, ORANGE, 'APP B'),
                ('Eve',   WHITE, '#ccc', ''),
                ('Frank', WHITE, '#ccc', ''),
            ],
            'ptr_a': 'Ptr A → 1 (Bob)',
            'ptr_b': 'Ptr B → 3 (Dave)',
            'note': 'Ptr A at 1 (Bob).\nNext search starts at pos 2\n→ Carol\'s natural turn.',
        },
        {
            'title': 'Week 3 (Carol on vacation)',
            'subtitle': 'Pointer A HOLDS at Carol',
            'members': [
                ('Alice', WHITE, '#ccc', ''),
                ('Bob',   '#fce4e4', RED, 'skip: did A wk2'),
                ('Carol', GRAY, '#999', 'VACATION'),
                ('Dave',  '#fce4e4', RED, 'skip: did B wk2'),
                ('Eve',   LIGHT_BLUE, BLUE, 'APP A (sub)'),
                ('Frank', LIGHT_ORANGE, ORANGE, 'APP B'),
            ],
            'ptr_a': 'Ptr A → 1 (HELD)',
            'ptr_b': 'Ptr B → 5 (Frank)',
            'note': 'start = pos 2 = Carol → VACATION\n→ HOLD. Ptr stays at 1.\nEve substitutes for App A.',
        },
        {
            'title': 'Week 4 (Carol still out)',
            'subtitle': 'Pointer A still held at Carol',
            'members': [
                ('Alice', LIGHT_ORANGE, ORANGE, 'APP B'),
                ('Bob',   WHITE, '#ccc', ''),
                ('Carol', GRAY, '#999', 'VACATION'),
                ('Dave',  LIGHT_BLUE, BLUE, 'APP A (sub)'),
                ('Eve',   '#fce4e4', RED, 'skip: did A wk3'),
                ('Frank', '#fce4e4', RED, 'skip: did B wk3'),
            ],
            'ptr_a': 'Ptr A → 1 (HELD)',
            'ptr_b': 'Ptr B → 0 (Alice)',
            'note': 'start = pos 2 = Carol → VACATION\n→ HOLD re-armed. Ptr stays at 1.\nDave substitutes again.',
        },
        {
            'title': 'Week 5 (Carol returns!)',
            'subtitle': 'Carol is first in line',
            'members': [
                ('Alice', '#fce4e4', RED, 'skip: did B wk4'),
                ('Bob',   LIGHT_ORANGE, ORANGE, 'APP B'),
                ('Carol', LIGHT_PURPLE, PURPLE, 'APP A ★'),
                ('Dave',  '#fce4e4', RED, 'skip: did A wk4'),
                ('Eve',   WHITE, '#ccc', ''),
                ('Frank', WHITE, '#ccc', ''),
            ],
            'ptr_a': 'Ptr A → 2 (Carol) ★',
            'ptr_b': 'Ptr B → 1 (Bob)',
            'note': 'start = pos 2 = Carol → AVAILABLE\n→ Carol assigned! Turn deferred,\nnot lost. Ptr advances to 2.',
        },
    ]

    for ax, wd in zip(axes, weeks_data):
        ax.set_xlim(-0.5, 3.5)
        ax.set_ylim(-2.5, 7.5)
        ax.axis('off')
        ax.set_title(f"{wd['title']}\n{wd['subtitle']}", fontsize=11, fontweight='bold')

        for i, (name, color, edge, note) in enumerate(wd['members']):
            y = 5.5 - i
            rect = mpatches.FancyBboxPatch((0.1, y - 0.3), 1.1, 0.6,
                                            boxstyle='round,pad=0.08',
                                            facecolor=color, edgecolor=edge, linewidth=1.5)
            ax.add_patch(rect)
            style = 'italic' if note == 'VACATION' else 'normal'
            ax.text(0.65, y, name, ha='center', va='center', fontsize=10,
                    fontweight='bold', style=style)
            if note:
                if 'VACATION' in note:
                    ncolor = '#999'
                elif 'APP A' in note:
                    ncolor = BLUE if '★' not in note else PURPLE
                elif 'APP B' in note:
                    ncolor = ORANGE
                else:
                    ncolor = RED
                ax.text(1.3, y, note, ha='left', va='center', fontsize=8,
                        color=ncolor, fontweight='bold')

        # Pointer status
        ptr_a_color = PURPLE if 'HELD' in wd['ptr_a'] or '★' in wd['ptr_a'] else BLUE
        ax.text(0.1, -0.3, wd['ptr_a'], fontsize=8.5, color=ptr_a_color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=LIGHT_BLUE, edgecolor=ptr_a_color, lw=1.5))
        ax.text(0.1, -0.85, wd['ptr_b'], fontsize=8.5, color=ORANGE, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=LIGHT_ORANGE, edgecolor=ORANGE, lw=1.5))

        if wd['note']:
            ax.text(0.1, -1.6, wd['note'], fontsize=8.5, color='#555', va='top',
                    style='italic',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#f9f9f9', edgecolor='#ddd'))

    # Bottom legend
    legend_items = [
        (LIGHT_BLUE, BLUE, 'Assigned App A'),
        (LIGHT_ORANGE, ORANGE, 'Assigned App B'),
        (LIGHT_PURPLE, PURPLE, 'Deferred turn fulfilled ★'),
        ('#fce4e4', RED, 'Skipped (cool-down)'),
        (GRAY, '#999', 'On vacation (ptr holds)'),
    ]
    fig.subplots_adjust(bottom=0.12)
    for i, (fc, ec, label) in enumerate(legend_items):
        x = 0.06 + i * 0.19
        rect = mpatches.FancyBboxPatch((x, 0.02), 0.025, 0.03,
                                        boxstyle='round,pad=0.004',
                                        facecolor=fc, edgecolor=ec, linewidth=1.5,
                                        transform=fig.transFigure)
        fig.patches.append(rect)
        fig.text(x + 0.032, 0.035, label, fontsize=8.5, va='center')

    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
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
    """Bar chart + rotation table showing fair distribution over 12 weeks."""
    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor(WHITE)
    fig.suptitle('Diagram 7: Fairness With Label Rotation (12 Weeks)\n'
                 'Every member does every app equally — labels swap at the half-cycle',
                 fontsize=15, fontweight='bold', y=0.98)

    # --- Top: rotation table showing the two 6-week cycles ---
    ax_table = fig.add_axes([0.05, 0.52, 0.9, 0.40])
    ax_table.axis('off')

    # Actual schedule produced by the algorithm (verified):
    # Cycle 1 (wks 1-3): Ptr A→App A, Ptr B→App B
    # Cycle 2 (wks 4-6): Ptr A→App B, Ptr B→App A  (labels swapped)
    schedule = [
        ('1', 'Alice', 'Bob'),   ('2', 'Carol', 'Dave'),  ('3', 'Eve', 'Frank'),
        ('4', 'Bob', 'Alice'),   ('5', 'Dave', 'Carol'),  ('6', 'Frank', 'Eve'),
        ('7', 'Alice', 'Bob'),   ('8', 'Carol', 'Dave'),  ('9', 'Eve', 'Frank'),
        ('10', 'Bob', 'Alice'),  ('11', 'Dave', 'Carol'), ('12', 'Frank', 'Eve'),
    ]

    col_labels = ['Week', 'App A', 'App B']
    cell_text = [[w, a, b] for w, a, b in schedule]
    cell_colors = []
    for i, (w, a, b) in enumerate(schedule):
        cycle = 'first' if (i % 6) < 3 else 'second'
        bg_a = LIGHT_BLUE if cycle == 'first' else '#e8d5f5'   # purple tint for swapped
        bg_b = LIGHT_ORANGE if cycle == 'first' else '#d5ebd5'  # green tint for swapped
        cell_colors.append([WHITE, bg_a, bg_b])

    table = ax_table.table(cellText=cell_text, colLabels=col_labels,
                           cellColours=cell_colors, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.6)

    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(DARK)
        cell.set_text_props(color=WHITE, fontweight='bold')

    # Cycle boundary markers
    for row_idx in [4, 10]:  # rows after week 3 and 9 (1-indexed with header)
        for j in range(len(col_labels)):
            cell = table[row_idx, j]
            cell.set_edgecolor(GREEN)
            cell.set_linewidth(2)

    ax_table.text(0.5, -0.05,
                  'Blue/Orange = normal pointer-to-app mapping  |  '
                  'Purple/Green = labels swapped (cycle 2)  |  '
                  'Green border = swap boundary',
                  ha='center', va='top', fontsize=9, style='italic', color='#555',
                  transform=ax_table.transAxes)

    # --- Bottom: bar chart showing equal 2/2 split ---
    ax_bar = fig.add_axes([0.08, 0.06, 0.85, 0.38])

    members = SHORT
    # With label rotation: each member gets App A twice and App B twice in 12 weeks
    app_a_counts = [2, 2, 2, 2, 2, 2]
    app_b_counts = [2, 2, 2, 2, 2, 2]

    x = np.arange(len(members))
    width = 0.35

    bars1 = ax_bar.bar(x - width/2, app_a_counts, width, label='App A', color=BLUE, edgecolor='white')
    bars2 = ax_bar.bar(x + width/2, app_b_counts, width, label='App B', color=ORANGE, edgecolor='white')

    ax_bar.set_ylabel('Assignments (12 weeks)', fontsize=11)
    ax_bar.set_xlabel('Team Members', fontsize=11)
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(members, fontsize=11)
    ax_bar.legend(fontsize=11, loc='upper right')
    ax_bar.set_ylim(0, 5)
    ax_bar.set_yticks([0, 1, 2, 3, 4])
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)

    for bar in bars1:
        if bar.get_height() > 0:
            ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(int(bar.get_height())), ha='center', fontsize=10, fontweight='bold',
                        color=BLUE)
    for bar in bars2:
        if bar.get_height() > 0:
            ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(int(bar.get_height())), ha='center', fontsize=10, fontweight='bold',
                        color=ORANGE)

    ax_bar.text(0.5, -0.15,
                'Label rotation swaps pointer-to-app mapping every N/K = 3 weeks.\n'
                'Result: perfectly equal distribution — every member does every app the same number of times.',
                ha='center', va='top', fontsize=9, style='italic', color='#555',
                transform=ax_bar.transAxes)

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
