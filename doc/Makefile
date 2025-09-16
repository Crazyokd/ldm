fmt ?= svg

watch: overview.d2
	@pidof -q d2 && pkill -x d2 || true
	d2 -s -w -p 34200 $< >d2.log 2>&1 &

${fmt}: overview.d2
	d2 -s $< $<.$@

clean:
	rm -rfv *.svg *.pdf *.png *.log
