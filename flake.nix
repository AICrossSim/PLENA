{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        rustPlatform = pkgs.rustPlatform;
        llvm14 = pkgs.llvmPackages_14;
      in
      rec {
        # ---------- Dev Shell for the whole repo ----------
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # --- Verilog/SystemVerilog toolchain ---
            verilator
            verible

            # --- Compilers / build tools ---
            gcc
            gnumake
            cmake
            ninja
            pkg-config
            autoconf
            flex
            bison
            ccache
            help2man

            # --- LLVM/Clang (plus specific 14.x, if needed) ---
            clang
            llvmPackages.clang-unwrapped
            llvmPackages.lld
            clang-tools
            llvm14.clang
            llvm14.lld

            # --- General dev / utils ---
            git
            wget
            unzip
            vim
            htop
            xdg-utils
            parallel
            just

            # --- Crypto / SSL / IDN ---
            openssl
            libidn

            # --- Performance / NUMA ---
            gperftools
            numactl

            # --- Python (two versions) ---
            python312
            python312Packages.pip
            python312Packages.sphinx
            python313
            python313Packages.pip

            # --- Math / BLAS / LAPACK / Fortran ---
            openblas
            lapack
            gfortran

            # --- Graphics / docs ---
            graphviz

            # --- Multimedia / FFmpeg (libavformat, libswscale) ---
            ffmpeg

            # --- SDL 1.2 + SDL2 stacks ---
            SDL
            SDL_image
            SDL_mixer
            SDL_ttf
            smpeg
            portmidi
            SDL2
            SDL2_image
            SDL2_mixer
            SDL2_ttf
            xorg.libXtst
          ];

          nativeBuildInputs = with pkgs; [
            rustup
            uv
          ];

          shellHook = ''
            echo ">>> Toolchain versions:"
            echo "Verilator:    $(verilator --version 2>/dev/null || echo not found)"
            echo "Verible:      $(verible-verilog-format --version 2>/dev/null || echo not found)"
            echo "Clang:        $(clang --version | head -n1 2>/dev/null || echo not found)"
            echo "GCC:          $(gcc --version | head -n1 2>/dev/null || echo not found)"
            echo "CMake:        $(cmake --version | head -n1 2>/dev/null || echo not found)"
            echo "Python 3.12:  $(python3.12 --version 2>/dev/null || echo not found)"
            echo "Python 3.13:  $(python3.13 --version 2>/dev/null || echo not found)"
            echo "FFmpeg:       $(ffmpeg -version | head -n1 2>/dev/null || echo not found)"
          '';
        };

        # ---------- (Optional) Build the simulator as a Nix package ----------
        #
        # This assumes your Rust binary crate lives in ./behavioral_simulator
        # and produces an executable (e.g., `aria-sim`); adjust name if needed.
        #
        packages.behavioral-simulator = rustPlatform.buildRustPackage {
          pname = "behavioral-simulator";
          version = "0.1.0";
          src = pkgs.lib.cleanSource ./behavioral_simulator;

          # Use the Cargo.lock from that subdir:
          cargoLock = {
            lockFile = ./behavioral_simulator/Cargo.lock;
          };

          # If build complains about missing libs (e.g., libtorch), add
          # them to buildInputs and/or set RPATH/LD_LIBRARY_PATH here.
          buildInputs = with pkgs; [
            # Example: add system libs required by your crate
            # openblas lapack
          ];

          # If you need environment vars during build, set them here.
          # RUSTFLAGS = "-C target-cpu=native";
        };

        # Make `nix build` with no attr pick the simulator by default
        packages.default = packages.behavioral-simulator;

        # Formatter
        formatter = pkgs.alejandra;
      }
    );
}
