from pathlib import Path


class AsmPerfTracker:
    def __init__(self, test_name):
        self.test_name = test_name
        self.stats = []
        self.assembly_code = ""

    def add_section(self, section_name, code):
        """Add a section of assembly code and track its line count."""
        line_count = len(code.splitlines())
        self.stats.append(f"{section_name}: {line_count} lines")
        print(f"{section_name}: {line_count} lines")
        self.assembly_code += code
        return code

    def get_code(self):
        """Get the full assembly code."""
        return self.assembly_code

    def write_stats(self, output_file="perf.log"):
        """Write performance stats to file."""
        total_lines = len(self.assembly_code.splitlines())
        self.stats.append(f"\nTotal assembly lines: {total_lines}")

        # Print summary to console
        print("\n" + "=" * 60)
        print(f"{self.test_name} Assembly Generation Stats")
        print("=" * 60)
        for stat in self.stats:
            print(stat)
        print("=" * 60)

        # Write to perf.log in root
        perf_file_path = Path(__file__).parent.parent.parent / output_file
        with open(perf_file_path, "w") as f:
            f.write(f"{self.test_name} Assembly Generation Stats\n")
            f.write("=" * 40 + "\n")
            f.write("\n".join(self.stats))
        print(f"\nPerformance stats written to {perf_file_path}")
