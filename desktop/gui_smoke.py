"""Full interface smoke test under Linux Xvfb; real repo datasets required."""
from energymap import EnergyMapApp


def main():
    app = EnergyMapApp()
    try:
        app.update()
        assert len(app.tree.get_children()) == 459, 'Canonical All sites registry not loaded'
        assert app.view.get() == 'All sites'
        assert len(app.catalogs['All ≥1 GW']) == 373, 'Threshold filter must include development records'
        assert len(app.catalogs['Data centers']) == 156
        assert len(app.catalogs['Data centers ≥1 GW']) == 70
        app.view.set('All ≥1 GW')
        app._change_view()
        assert len(app.tree.get_children()) == 373
        first = app.visible[app.tree.get_children()[0]]['capacityMW']
        second = app.visible[app.tree.get_children()[1]]['capacityMW']
        assert first >= second, 'Default MW sort is not descending'
        app.change_sort('capacity')
        assert app.visible[app.tree.get_children()[0]]['capacityMW'] <= 1000
        app.change_sort('capacity')
        assert len(app.atlas.states) >= 50, 'US state boundaries missing'
        assert len(app.atlas.countries) >= 175, 'World country boundaries missing'
        assert len(app.atlas.point_hits) >= 270, 'Power-generation markers missing'
        assert app.cols == ('rank', 'name', 'state', 'category', 'capacity')
        assert app.tree.heading('rank', 'text') == 'Row #'
        assert str(app.tree.item(app.tree.get_children()[0], 'values')[0]) == '1'
        assert app.brand_label.cget('text') == 'BitcoinVersus.tech'
        assert app.brand_label.cget('fg').lower() == '#39ff14'
        assert app.brand_label.cget('bg').lower() == '#080808'
        assert app.info.cget('wrap') == 'word'
        app.atlas.mode.set('World globe')
        app.atlas.change_mode()
        app.update()
        assert app.atlas.canvas.find_all(), 'Globe failed to render'
        assert app.atlas.point_hits, 'Visible hemisphere must include US pins at initial angle'
        start = app.atlas.globe_lon
        app.atlas._spin()
        assert app.atlas.globe_lon != start, 'Globe did not rotate'
        app.atlas.stop_spin()
        app.atlas.mode.set('United States')
        app.atlas.change_mode()
        app.view.set('National top 25')
        app._change_view()
        assert len(app.tree.get_children()) == 25, 'Calculated Top 25 must include 25 campuses'
        assert app.visible[app.tree.get_children()[0]]['capacityMW'] == 11000
        assert app.tree.heading('rank', 'text') == 'Top 25 #'
        first_id = app.tree.get_children()[0]
        assert str(app.tree.item(first_id, 'values')[0]) == str(
            app.visible[first_id]['nationalComputedRank'])
        assert all(row.get('recordType') == 'Data centers / campuses'
                   for row in app.visible.values())
        assert any(r.get('markerKind') == 'locality' for r in app.visible.values())
        app.update()
        assert app.atlas.point_hits, 'National Top 25 must show approximate or regional markers'
        app.view.set('State rankings')
        app._change_view()
        assert len(app.tree.get_children()) == 459, 'State rankings must include every site'
        assert app.tree.heading('rank', 'text') == 'State #'
        assert all(str(app.tree.item(key, 'values')[0]) == str(
            app.visible[key].get('stateRank')
            if app.visible[key].get('stateRank') is not None else 'N/R')
            for key in app.tree.get_children())
        assert {r['id'] for r in app.visible.values()} == {
            r['id'] for r in app.catalogs['All sites']}
        states = list(app.state_combo['values'])
        assert len(set(states)) == 51, 'Expected All states plus 50 states'
        for state in states:
            if state == 'All states':
                continue
            app.state.set(state)
            app.refresh()
            expected = [r for r in app.catalogs['All sites'] if r['state'] == state]
            assert len(app.tree.get_children()) == len(expected), (
                f'State rankings omitted facilities in {state}'
            )
            assert all(r['state'] == state for r in app.visible.values())
            cap = [r['capacityMW'] for r in app.visible.values()
                   if isinstance(r.get('capacityMW'), (int, float))]
            assert cap == sorted(cap, reverse=True), f'Bad capacity order: {state}'
            plotted = len(app.atlas.point_hits)
            located = sum(app.atlas._coordinates(r) is not None
                          for r in app.visible.values())
            assert 0 <= plotted <= located, (
                f'State map has non-location markers for {state}: '
                f'{plotted} dots but only {located} source locations'
            )
            # Projects without source location stay in the table; no state
            # square or manufactured individual marker is permitted.
            for canvas_id in app.atlas.canvas.find_all():
                assert app.atlas.canvas.itemcget(canvas_id, 'fill') != '#7545a8', (
                    f'Old purple aggregate square still visible in {state}'
                )
        app.state.set('All states')
        app.view.set('Data centers')
        app._change_view()
        assert len(app.tree.get_children()) == 156, 'All state development sites must be browsable'
        app.update()
        assert sum(r.get('markerKind') == 'locality' for r in app.visible.values()) == 116
        assert len(app.atlas.point_hits) == 116, (
            'Data center map must have 116 town-reference dots and no state squares'
        )
        assert '40 unlocated' in app.atlas.note.get()
        assert all(app.atlas.canvas.type(canvas_id) != 'rectangle'
                   or app.atlas.canvas.itemcget(canvas_id, 'fill') != '#7545a8'
                   for canvas_id in app.atlas.canvas.find_all())
        app.view.set('National top 25')
        app._change_view()
        assert len(app.tree.get_children()) == 25, 'All Top 25 projects must be browsable'
        app.change_sort('rank')
        assert app.visible[app.tree.get_children()[0]]['nationalComputedRank'] == 1
        assert app.visible[app.tree.get_children()[-1]]['nationalComputedRank'] == 25
        app.view.set('State rankings')
        app._change_view()
        app.state.set('Texas')
        app.refresh()
        app.change_sort('rank')
        state_ranks = [r['stateRank'] for r in app.visible.values()
                       if r.get('stateRank') is not None]
        assert state_ranks == sorted(state_ranks), 'State rank heading did not sort ascending'
        app.view.set('All sites')
        app._change_view()
        app.category.set('Data centers / campuses')
        app.refresh()
        assert len(app.tree.get_children()) == 156, 'Category filter leaked power plants'
        assert sum(x.get('markerKind') == 'locality' for x in app.visible.values()) == 116
        app.category.set('Power generation')
        app.refresh()
        assert len(app.tree.get_children()) == 303, 'Power generation filter failed'
        assert len(app.atlas.point_hits) >= 270, 'Power generation map dots disappeared'
        app.category.set('All categories')
        app.search.set('does-not-match-any-record-ever')
        app.update()
        assert not app.tree.get_children(), 'Search did not filter rows'
        app.search.set('')
        app.update()
        assert app.tree.get_children(), 'Clear search failed'
        for size in ('960x640', '1000x640', '1280x800'):
            app.geometry(size)
            app.update()
            visible_width = app.tree.winfo_width()
            column_total = sum(app.tree.column(column, 'width') for column in app.cols)
            assert column_total <= visible_width, (
                f'Table columns overflow at {size}: {column_total} > {visible_width}'
            )
            assert app.tree.xview()[1] > .99, (
                f'Horizontal scrolling still needed at {size}: {app.tree.xview()}'
            )
            assert app.atlas.canvas.winfo_width() > 250
            assert app.tree.winfo_width() > 250, (
                f'{size}: tree={app.tree.winfo_width()}, pane={app.pane.winfo_width()}, '
                f'sash={app.pane.sashpos(0)}, map={app.atlas.canvas.winfo_width()}, '
                f'root={app.winfo_width()}, footer={app.status_label.winfo_width()}'
            )
        assert app.brand_label.winfo_rootx() < app.tree.winfo_rootx() + 20
        assert app.brand_label.winfo_rooty() > app.tree.winfo_rooty()
        print('EnergyMap UI smoke: fitted columns, ranking labels, branded footer, maps and categories passed')
    finally:
        app.destroy()


if __name__ == '__main__':
    main()
