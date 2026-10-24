import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.interactive.SysMLInteractiveResult;

/**
 * Parses and validates SysML v2 textual models with the same engine as the Jupyter kernel (the OMG pilot implementation), without Jupyter.
 *
 * Usage: java -cp <kernel>/'*' SysmlCheck.java <sysml.library dir> <file>... [-- <file>...]
 * Every group of files (separated by "--") is loaded in order into a fresh session, as the cells of a notebook would be, so a later file may import the
 * packages of an earlier one. Prints the issues of each file and exits with 1 if any file has an error, 2 if the library or a file cannot be read.
 */
public class SysmlCheck {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: SysmlCheck <sysml.library dir> <file>... [-- <file>...]");
            System.exit(2);
        }
        List<List<String>> groups = new ArrayList<>();
        groups.add(new ArrayList<>());
        for (int i = 1; i < args.length; i++) {
            if (args[i].equals("--")) {
                groups.add(new ArrayList<>());
            } else {
                groups.get(groups.size() - 1).add(args[i]);
            }
        }
        int files = 0, failed = 0, warned = 0;
        for (List<String> group : groups) {
            if (group.isEmpty()) {
                continue;
            }
            SysMLInteractive session = SysMLInteractive.createInstance();
            session.loadLibrary(args[0]);
            for (String file : group) {
                String text;
                try {
                    text = Files.readString(Path.of(file));
                } catch (Exception e) {
                    System.err.println("cannot read " + file + ": " + e.getMessage());
                    System.exit(2);
                    return;
                }
                SysMLInteractiveResult result = session.process(text);
                files++;
                if (result.getException() != null) {
                    System.out.println("FAIL " + file + "\n" + result.formatException());
                    failed++;
                } else if (result.hasErrors()) {
                    System.out.println("FAIL " + file + "\n" + result.formatIssues());
                    failed++;
                } else if (result.hasWarnings()) {
                    System.out.println("warn " + file + "\n" + result.formatIssues());
                    warned++;
                } else {
                    System.out.println("ok   " + file);
                }
            }
        }
        System.out.println(files + " file(s), " + failed + " with errors, " + warned + " with warnings");
        System.exit(failed > 0 ? 1 : 0);
    }
}
