package com.crapi.utils;

import java.util.List;
import java.util.Random;

/**
 * A credit card number generator.
 * Adapted from <a href="https://gist.github.com/josefeg/5781824">this GitHub Gist</a>.
 */
public class CreditCardNumberGenerator {

    public static String generate(Random random) {
        // List of popular credit card BINs
        List<String> creditCardBins = List.of(
                "411111", // Visa
                "601111", // Discover
                "521402", // MasterCard
                "342562" // American Express
        );
        String bin = creditCardBins.get(random.nextInt(creditCardBins.size()));
        return generate(bin, 16, random);
    }

    /**
     * Generates a credit card number.
     *
     * @param bin    The bank identification number, a set of digits at the start of the credit card
     *               number, used to identify the bank that is issuing the credit card.
     * @param length The total length (i.e. including the BIN) of the credit card number.
     * @return A randomly generated, valid, credit card number.
     */
    public static String generate(String bin, int length, Random random) {
        int randomNumberLength = length - bin.length() - 1;
        StringBuilder builder = new StringBuilder(bin);
        for (int i = 0; i < randomNumberLength; i++) {
            int digit = random.nextInt(10);
            builder.append(digit);
        }
        int checkDigit = getCheckDigit(builder.toString());
        builder.append(checkDigit);
        return builder.toString();
    }

    /**
     * Generates the check digit required to make the given credit card number
     * valid (i.e. pass the Luhn check).
     * @see <a href="https://en.wikipedia.org/wiki/Luhn_algorithm">Luhn algorithm
     * on Wikipedia</a>
     * @param number The credit card number for which to generate the check digit.
     * @return The check digit required to make the given credit card number
     * valid.
     */
    private static int getCheckDigit(String number) {
        int sum = 0;
        for (int i = number.length() - 1; i >= 0; --i) {
            int digit = number.charAt(i) - '0';
            int weight = (number.length() - i & 1) + 1;
            digit *= weight;
            if (digit > 9) {
                digit -= 9;
            }
            sum += digit;
        }
        return (10 - sum % 10) % 10;
    }
}
